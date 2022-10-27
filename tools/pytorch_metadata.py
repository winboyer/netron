''' TorchScript metadata script '''

import collections
import json
import os
import re
import sys

root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(root_dir)
sys.pycache_prefix = os.path.join(root_dir, 'dist', 'pycache', 'test', 'backend')
pytorch = __import__('source.pytorch').pytorch

source_dir = os.path.join(root_dir, 'source')
third_party_dir = os.path.join(root_dir, 'third_party')
metadata_file = os.path.join(source_dir, 'pytorch-metadata.json')
pytorch_source_dir = os.path.join(third_party_dir, 'source', 'pytorch')

def _read(path):
    with open(path, 'r', encoding='utf-8') as file:
        return file.read()

def _write(path, content):
    with open(path, 'w', encoding='utf-8') as file:
        file.write(content)

def _read_metadata():
    metadata = json.loads(_read(metadata_file))
    return dict(map(lambda item: [ item['name'], item ], metadata))

def _write_metadata(value):
    metadata = list(collections.OrderedDict(sorted(value.items())).values())
    content = json.dumps(metadata, indent=2, ensure_ascii=False)
    content = re.sub(r'\s {8}', ' ', content)
    content = re.sub(r',\s {8}', ', ', content)
    content = re.sub(r'\s {6}}', ' }', content)
    _write(metadata_file, content)

schema_source_files = [
    ('aten/src/ATen/native/native_functions.yaml',
        re.compile(r'-\s*func:\s*(.*)', re.MULTILINE), 'aten::'),
    ('aten/src/ATen/native/quantized/library.cpp',
        re.compile(r'TORCH_SELECTIVE_SCHEMA\("(.*)"\)', re.MULTILINE)),
    ('aten/src/ATen/native/xnnpack/RegisterOpContextClass.cpp',
        re.compile(r'TORCH_SELECTIVE_SCHEMA\("(.*)"', re.MULTILINE)),
    ('torch/csrc/jit/runtime/register_prim_ops_fulljit.cpp',
        re.compile(r'(aten::.*->\s*Tensor)', re.MULTILINE)),
    ('torch/csrc/jit/passes/shape_analysis.cpp',
        re.compile(r'(aten::.*->\s*Tensor)', re.MULTILINE)),
    ('caffe2/operators/copy_op.cc',
        re.compile(r'(_caffe2::.*->\s*Tensor)', re.MULTILINE)),
    ('caffe2/operators/batch_permutation_op.cc',
        re.compile(r'(_caffe2::.*->\s*Tensor)', re.MULTILINE)),
    ('caffe2/operators/collect_and_distribute_fpn_rpn_proposals_op.cc',
        re.compile(r'"(_caffe2::[\w+]*\([\w"\s\[\],]*\)\s*->\s*\([\w"\s\[\],]*\))"', re.MULTILINE)),
    ('caffe2/operators/box_with_nms_limit_op.cc',
        re.compile(r'"(_caffe2::[\w+]*\([\w"\s\[\],]*\)\s*->\s*\([\w"\s\[\],]*\))"', re.MULTILINE)),
    ('caffe2/operators/bbox_transform_op.cc',
        re.compile(r'"(_caffe2::[\w+]*\([\w"\s\[\],]*\)\s*->\s*\([\w"\s\[\],]*\))"', re.MULTILINE)),
    ('caffe2/operators/generate_proposals_op.cc',
        re.compile(r'"(_caffe2::[\w+]*\([\w"\s\[\],]*\)\s*->\s*\([\w"\s\[\],]*\))"', re.MULTILINE)),
    ('caffe2/operators/roi_align_op.cc',
        re.compile(r'"(_caffe2::[\w+]*\([\w"\s\[\],]*\)\s*->.*)"', re.MULTILINE))
]

def _metadata():

    types = _read_metadata()

    _write_metadata(types)

    for key in list(types.keys()):
        if key.startswith('torch.nn'):
            types.pop(key)

    for entry in schema_source_files:
        path = os.path.join(pytorch_source_dir, entry[0])
        content = _read(path)
        for value in entry[1].findall(content):
            value = re.sub(r'\n|\r|\s*"', '', value) if value.startswith('_caffe2::') else value
            definition = entry[2] + value if len(entry) > 2 else value
            schema = pytorch.Schema(definition)
            if schema.name in types:
                # value = types[schema.name]
                # if len(schema.arguments) != len(value['inputs']):
                #     pass
                types.pop(schema.name)

    # print('\n'.join(list(types.keys())))

def main(): # pylint: disable=missing-function-docstring
    _metadata()

if __name__ == '__main__':
    main()
