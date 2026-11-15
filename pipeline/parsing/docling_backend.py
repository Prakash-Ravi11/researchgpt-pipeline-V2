"""Lazy comparison adapter; predictions remain proposals until structure review.

Install only in an isolated candidate runtime. It does not rewrite source
chunks, invent canonical offsets, or mark model-produced cells VERIFIED.
"""
class DoclingProposalParser:
    identity="docling_tableformer_accurate"

    def __init__(self,path,assets,ocr=False):
        self.path,self.assets,self.ocr=path,assets,ocr

    def reconstruct(self,document,doc,chunks):
        from docling.document_converter import DocumentConverter,PdfFormatOption
        from docling.datamodel.base_models import InputFormat
        from docling.datamodel.pipeline_options import PdfPipelineOptions,TableFormerMode
        from docling.datamodel.accelerator_options import AcceleratorOptions,AcceleratorDevice
        options=PdfPipelineOptions(do_table_structure=True,do_ocr=self.ocr,artifacts_path=self.assets)
        options.table_structure_options.mode=TableFormerMode.ACCURATE
        options.table_structure_options.do_cell_matching=True
        options.accelerator_options=AcceleratorOptions(device=AcceleratorDevice.CUDA)
        result=DocumentConverter(format_options={InputFormat.PDF:PdfFormatOption(pipeline_options=options)}).convert(self.path)
        doc['external_structure_proposal']={"status":"EXTERNAL_PROPOSAL","parser":self.identity,
            "ocr_enabled":self.ocr,"document":result.document.export_to_dict()}
        return []
