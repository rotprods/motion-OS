from src.graph.scheduler import GraphScheduler,Job
from src.qa.multimodal_critic import FixtureProvider
from src.qa.release import release_gate
def test_scheduler_dependencies():
 s=GraphScheduler();s.add(Job('a','render','PENDING',10,[],{}));s.add(Job('b','splice','PENDING',5,['a'],{}));assert [j.id for j in s.ready()]==['a'];s.mark('a','DONE');assert [j.id for j in s.ready()]==['b']
def test_fixture_critic_is_non_authoritative():
 c=FixtureProvider().evaluate('fake.mp4',{});assert c.authoritative is False;assert release_gate({'score':9.9,'defects':[]},'fixture_non_authoritative')['verdict']=='BLOCK'
def test_release_blocks_fixture():
 c=FixtureProvider(score=9.9).evaluate('fake.mp4',{});assert c.authoritative is False;assert release_gate({'score':c.score,'defects':[]},'fixture_non_authoritative')['verdict']=='BLOCK'
