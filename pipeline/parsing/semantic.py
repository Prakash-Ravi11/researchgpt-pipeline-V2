"""Conservative caption/column relation builder, independent of cell numbers.

Benchmark names must be explicit caption identifiers or labeled benchmarks.
Language aliases are a closed vocabulary: both printed header and full caption
phrase are retained as evidence. No nearby-number or document-specific rules.
Multiple benchmark scopes abstain; no unrecorded dataset aliases are guessed.
"""
import re

from shared.schemas import EvidenceSpan, EvidenceRelation, SemanticBinding

LANGUAGES = {
    "en":"english", "de":"german", "fr":"french", "es":"spanish",
    "it":"italian", "nl":"dutch", "pt":"portuguese", "ru":"russian",
    "zh":"chinese", "ja":"japanese", "ar":"arabic", "cs":"czech", "fi":"finnish",
}


def _within(span, text, role, start):
    ref=span.reference.model_copy(update={"char_start":span.reference.char_start+start,
                                         "char_end":span.reference.char_start+start+len(text)})
    words=[w for w in getattr(span.reference,"source_words",[]) if w["text"]==text]
    return EvidenceSpan(span_id=f"{ref.chunk_id}@{ref.char_start}:{ref.char_end}:{role}",
        role=role,text=text,reference=ref,bbox=words[0]["bbox"] if len(words)==1 else span.bbox)


def _benchmark_mentions(text):
    patterns=[
        r"\b(?:benchmark|dataset|corpus|test set)\s*[:=]\s*([A-Za-z][A-Za-z0-9_.-]*(?:[ ](?:19|20)\d{2})?)",
        r"\b([A-Za-z][A-Za-z0-9_.-]*\d[A-Za-z0-9_.-]*)\s+(?:tests?|benchmark|dataset|corpus)\b",
        r"\b([A-Z][A-Za-z_-]{1,20}\s+(?:19|20)\d{2})\s+(?:benchmark|dataset|tests?|test set)\b",
        r"\b([A-Z][A-Za-z0-9_.-]+)\s+(?:benchmark|dataset|corpus|test set)\b",
    ]
    found={}
    for pattern in patterns:
        for m in re.finditer(pattern,text):found[(m.start(1),m.end(1))]=m.group(1)
    return [(start,end,name) for (start,end),name in sorted(found.items())]


def bind_bundle(bundle, chunks=()):
    """Derive semantic relations only inside this validated caption/header scope."""
    result=bundle.model_copy(deep=True)
    for span in result.spans:
        if span.bbox is None:span.bbox=getattr(span.reference,"source_bbox",None)
    roles={s.role:s for s in result.spans}
    caption,leaf,metric=roles["caption"],roles["dataset"],roles["metric"]
    def unresolved(reason,ambiguous=False):
        result.semantic=SemanticBinding(status="AMBIGUOUS" if ambiguous else "UNRESOLVED",metric=metric.text,reason=reason)
        result.unresolved=[reason]
        return result
    code=re.fullmatch(r"([A-Za-z]{2,3})[-/]([A-Za-z]{2,3})",leaf.text)
    condition=None
    additions=[]
    if code:
        names=[LANGUAGES.get(c.lower()) for c in code.groups()]
        if not all(names):return unresolved("unknown_language_condition")
        phrases=[m for m in re.finditer(r"\b([A-Za-z]+)[ -]to[ -]([A-Za-z]+)\b",caption.text)
                 if [m[1].lower(),m[2].lower()]==names]
        if len(phrases)!=1:return unresolved("ambiguous_or_missing_caption_condition",len(phrases)>1)
        mentions=_benchmark_mentions(caption.text)
        if len(mentions)!=1:return unresolved("ambiguous_or_missing_caption_benchmark",len(mentions)>1)
        start,end,name=mentions[0]
        benchmark=_within(caption,name,"benchmark",start)
        condition=_within(caption,phrases[0][0],"condition",phrases[0].start())
        label=leaf.model_copy(update={"role":"condition_label","span_id":leaf.span_id+":condition_label"})
        additions=[benchmark,condition,label]
    else:
        matches=list(re.finditer(r"(?<!\w)"+re.escape(leaf.text)+r"(?!\w)",caption.text))
        if len(matches)!=1:return unresolved("ambiguous_or_missing_caption_benchmark",len(matches)>1)
        named=[m for m in _benchmark_mentions(caption.text) if m[2]==leaf.text]
        if len(named)!=1:return unresolved("column_label_is_not_a_named_benchmark",len(named)>1)
        # Direct dataset column; no synthetic task/condition is added.
        benchmark=_within(caption,matches[0][0],"benchmark",matches[0].start())
        additions=[benchmark]
    unit=None
    unit_match=re.search(r"\((%|ms|s|mm|cm|kg|FLOPs)\)",metric.text)
    if unit_match:
        unit=unit_match[1]
        additions.append(_within(metric,unit,"unit",unit_match.start(1)))
    relations=[EvidenceRelation(kind="caption_benchmark",from_span_id=caption.span_id,to_span_id=benchmark.span_id,table_id=bundle.table_id),
                EvidenceRelation(kind="header_metric",from_span_id=metric.span_id,to_span_id=leaf.span_id,table_id=bundle.table_id),
                EvidenceRelation(kind="row_value",from_span_id=roles["subject"].span_id,to_span_id=roles["value"].span_id,table_id=bundle.table_id),
                EvidenceRelation(kind="column_value",from_span_id=leaf.span_id,to_span_id=roles["value"].span_id,table_id=bundle.table_id)]
    if unit:
        relations.append(EvidenceRelation(kind="metric_unit",from_span_id=metric.span_id,
            to_span_id=next(s.span_id for s in additions if s.role=="unit"),table_id=bundle.table_id))
    if condition:
        relations.extend([
            EvidenceRelation(kind="caption_condition",from_span_id=caption.span_id,to_span_id=condition.span_id,table_id=bundle.table_id),
            EvidenceRelation(kind="header_condition",from_span_id=leaf.span_id,to_span_id=condition.span_id,table_id=bundle.table_id)])
    table_label=re.match(r"Table\s+\S+",caption.text)
    if table_label:
        label=table_label[0].rstrip(":.")
        mentions=[]
        for chunk in chunks:
            if chunk.page_or_node!=caption.reference.page_or_node or chunk.block_id==caption.reference.block_id:continue
            for match in re.finditer(r"[^.!?]+(?:[.!?]|$)",chunk.text):
                if re.search(re.escape(label)+r"(?!\d)",match[0]) and re.search(r"\b(?:our|we)\b",match[0],re.I):
                    parent=EvidenceSpan(span_id=chunk.chunk_id,role="prose",text=chunk.text,
                        reference=chunk.reference(),bbox=getattr(chunk,"source_bbox",None))
                    raw=match[0];left=len(raw)-len(raw.lstrip())
                    mentions.append(_within(parent,raw.strip(),"ownership",match.start()+left))
        if len(mentions)==1:
            additions.append(mentions[0])
            relations.append(EvidenceRelation(kind="table_mention",from_span_id=mentions[0].span_id,
                to_span_id=caption.span_id,table_id=bundle.table_id))
    result.spans.extend(additions)
    result.semantic=SemanticBinding(status="RESOLVED",benchmark=benchmark.text,condition=condition.text if condition else None,
        condition_label=leaf.text if condition else None,metric=metric.text,unit=unit,relations=relations)
    result.unresolved=[]
    return result


def bind_bundles(bundles, chunks=()):
    return [bind_bundle(b,chunks) for b in bundles]
