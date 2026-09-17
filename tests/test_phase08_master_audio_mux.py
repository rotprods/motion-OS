import pytest

from src.renderers.assembly import RenderArtifact, build_composite_plan, ffmpeg_assembly_argv


def _plan(*, audio_path='master.wav'):
    artifacts=[
        RenderArtifact('base','remotion','base with audio.mov',0,2000,1080,1920,30,False,('graph:base',),z_index=0),
        RenderArtifact('overlay','hyperframes','overlay;not-a-shell-command.mov',1500,2000,1080,1920,30,True,('graph:overlay',),z_index=6),
    ]
    return build_composite_plan(
        artifacts,
        width=1080,
        height=1920,
        fps=30,
        duration_ms=2000,
        audio_path=audio_path,
    )


def test_master_audio_is_the_only_mapped_audio_stream_and_is_exact_duration():
    plan=_plan(audio_path='master audio;$(touch never).wav')
    argv=ffmpeg_assembly_argv(plan,'final output.mp4')
    assert argv[:2] == ['ffmpeg','-n']
    assert argv.count('-i') == 3
    maps=[argv[index+1] for index,value in enumerate(argv[:-1]) if value=='-map']
    assert maps == ['[v1]','[mastera]']
    assert not any(value in {'0:a','0:a:0','1:a','1:a:0'} for value in maps)
    filter_graph=argv[argv.index('-filter_complex')+1]
    assert '[2:a:0]asetpts=PTS-STARTPTS,apad,atrim=duration=2.000[mastera]' in filter_graph
    assert plan['audio_integrity_policy'] == 'post_render_master_audio_required'


def test_no_master_audio_explicitly_disables_all_audio():
    plan=_plan(audio_path=None)
    argv=ffmpeg_assembly_argv(plan,'silent.mp4')
    assert argv.count('-i') == 2
    assert '-an' in argv
    assert plan['audio_integrity_policy'] == 'explicit_silence'


def test_single_video_uses_base_label_and_master_audio_input_index_one():
    plan=build_composite_plan(
        [RenderArtifact('base','remotion','base.mov',0,1000,1080,1920,30,False,('graph:base',),z_index=0)],
        width=1080,height=1920,fps=30,duration_ms=1000,audio_path='master.wav',
    )
    argv=ffmpeg_assembly_argv(plan,'out.mp4',video_codec='qualified-codec',audio_codec='qualified-audio')
    maps=[argv[index+1] for index,value in enumerate(argv[:-1]) if value=='-map']
    assert maps == ['[base0]','[mastera]']
    assert '[1:a:0]' in argv[argv.index('-filter_complex')+1]


def test_empty_paths_and_invalid_audio_contract_fail_closed():
    with pytest.raises(ValueError,match='empty_master_audio_path'):
        build_composite_plan(
            [RenderArtifact('base','remotion','base.mov',0,1000,1080,1920,30,False,('graph:base',))],
            width=1080,height=1920,fps=30,duration_ms=1000,audio_path='   ',
        )
    plan=_plan()
    plan['audio_policy']='renderer_audio_allowed'
    with pytest.raises(ValueError,match='unsupported audio policy'):
        ffmpeg_assembly_argv(plan,'out.mp4')
