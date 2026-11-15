"""Apply the same host verifier to remote proposals and a trusted local packet."""
import argparse
import hashlib
import json
from pathlib import Path
from pipeline.inference.replay import replay


def main():
    p=argparse.ArgumentParser();p.add_argument('packet',type=Path);p.add_argument('candidates',type=Path)
    p.add_argument('--expected-packet-sha256',required=True);p.add_argument('--output',type=Path,required=True)
    args=p.parse_args()
    if hashlib.sha256(args.packet.read_bytes()).hexdigest()!=args.expected_packet_sha256:
        raise ValueError('packet differs from the trusted locally exported input')
    result=replay(json.loads(args.packet.read_text(encoding='utf-8')),json.loads(args.candidates.read_text(encoding='utf-8')))
    args.output.write_text(result.model_dump_json(indent=2),encoding='utf-8')


if __name__=='__main__':main()
