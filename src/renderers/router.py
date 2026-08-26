from __future__ import annotations
from dataclasses import dataclass,asdict
from pathlib import Path
import shutil
@dataclass
class RendererCapability:
    name:str;available:bool;command:str|None;strengths:list[str];reason:str|None=None
def _command_available(cmd):return shutil.which(cmd) is not None
def detect_capabilities():
    hf_local=Path('node_modules/.bin/hyperframes').exists() or _command_available('hyperframes');rem_local=Path('node_modules/.bin/remotion').exists() or _command_available('remotion');ffmpeg=_command_available('ffmpeg')
    return [RendererCapability('hyperframes',hf_local,'hyperframes' if _command_available('hyperframes') else ('node_modules/.bin/hyperframes' if hf_local else None),['html','gsap','svg','kinetic_typography','procedural_motion'],None if hf_local else 'HyperFrames not installed locally; network installs are not assumed.'),RendererCapability('remotion',rem_local,'remotion' if _command_available('remotion') else ('node_modules/.bin/remotion' if rem_local else None),['react','deterministic_frames','exact_typography','media_compositing','parameterized_templates'],None if rem_local else 'Remotion not installed locally; network installs are not assumed.'),RendererCapability('native_prototype',ffmpeg,'ffmpeg' if ffmpeg else None,['offline','deterministic','fixture_rendering','qa_baselines'],None if ffmpeg else 'ffmpeg unavailable.')]
def choose_renderer(scene_requirements,capabilities=None):
    capabilities=capabilities or detect_capabilities();by={c.name:c for c in capabilities};wanted=[]
    if scene_requirements.get('heavy_svg') or scene_requirements.get('kinetic_type'):wanted.append('hyperframes')
    if scene_requirements.get('exact_ui') or scene_requirements.get('exact_text') or scene_requirements.get('media_composite'):wanted.append('remotion')
    wanted+=['hyperframes','remotion','native_prototype'];seen=set()
    for name in wanted:
        if name in seen:continue
        seen.add(name);cap=by.get(name)
        if cap and cap.available:return {'selected':name,'capability':asdict(cap),'fallback_used':name not in wanted[:1]}
    raise RuntimeError('No renderer available')
