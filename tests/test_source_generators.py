from src.renderers.source_generators import generate_hyperframes_project,generate_remotion_project
def test_source_generators(tmp_path):
 brief={'duration':10,'fps':30,'headline':'TEST'};style={'style_id':'x','palette':['#eee','#111'],'type':'serif'};beats=[];h=generate_hyperframes_project(tmp_path/'h',brief,style,beats);r=generate_remotion_project(tmp_path/'r',brief,style,beats);assert (h/'index.html').exists();assert (r/'src/MotionOS.tsx').exists()
