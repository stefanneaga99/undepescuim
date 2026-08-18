from scripts.river_segment_audit_lib import resolve_contract

def test_smallest_interval_wins():
    c=[{'slug':'wide','sectorStart':0,'sectorEnd':1},{'slug':'narrow','sectorStart':.4,'sectorEnd':.6}]
    assert resolve_contract(.5,c)['slug']=='narrow'

def test_voronoi_matches_course_frac():
    c=[{'slug':'up','course_frac':.1},{'slug':'down','course_frac':.9}]
    assert resolve_contract(.2,c)['slug']=='up'
    assert resolve_contract(.8,c)['slug']=='down'

def test_singleton_is_ui_fallback():
    assert resolve_contract(.5,[{'slug':'only'}]) is None
