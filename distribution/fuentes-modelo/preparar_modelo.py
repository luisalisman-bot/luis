"""Expose existing Whisper alignment attention without changing model weights.

Matches sherpa-onnx/scripts/whisper/export-onnx-with-attention.py's output contract.
Alignment head mask is OpenAI Whisper's published mask for base (MIT).
"""
from pathlib import Path
import ast, base64, gzip, shutil
import numpy as np
import onnx
from onnx import helper, numpy_helper, TensorProto
source=Path('work/whisper-base/sherpa-onnx-whisper-base')
dest=Path('work/model-whisper-base'); dest.mkdir(exist_ok=True)
module=ast.parse(Path('work/whisper-init.py').read_text())
mask=None
for node in module.body:
 if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='_ALIGNMENT_HEADS' for t in node.targets):
  mask=ast.literal_eval(node.value)['base']
heads=list(zip(*np.where(np.frombuffer(gzip.decompress(base64.b85decode(mask)),dtype=np.bool_).reshape(6,8))))
print('Alignment heads',heads)
m=onnx.load(source/'base-decoder.int8.onnx')
softmax=[n for n in m.graph.node if n.op_type=='Softmax']
assert len(softmax)==12, 'Expected self attention and cross attention for each layer'
outputs=[]
for layer in sorted(set(int(l) for l,h in heads)):
 indices=np.array([h for l,h in heads if l==layer],dtype=np.int64)
 key=f'alignment_heads_layer_{layer}'
 m.graph.initializer.append(numpy_helper.from_array(indices,name=key))
 out=f'alignment_weights_layer_{layer}'
 m.graph.node.append(helper.make_node('Gather',[softmax[2*layer+1].output[0],key],[out],axis=1,name=out))
 outputs.append(out)
m.graph.node.append(helper.make_node('Concat',outputs,['cross_attention_weights'],axis=1,name='alignment_attention_output'))
m.graph.output.append(helper.make_tensor_value_info('cross_attention_weights',TensorProto.FLOAT,['n_audio',len(heads),'n_tokens','T']))
onnx.checker.check_model(m)
onnx.save(m,dest/'base-decoder.int8.onnx')
e=onnx.load(source/'base-encoder.int8.onnx')
props={p.key:p.value for p in e.metadata_props}
props.update(version='2',n_alignment_heads=str(len(heads)),alignment_heads=','.join(f'{l}:{h}' for l,h in heads))
helper.set_model_props(e,props)
onnx.checker.check_model(e)
onnx.save(e,dest/'base-encoder.int8.onnx')
shutil.copy2(source/'base-tokens.txt',dest/'base-tokens.txt')
