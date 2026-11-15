from app.core.contingency import evaluate_contingency
from app.data.sites_catalog import get_sites_catalog
def test_contingency_passing_primary():
    res=evaluate_contingency('lola-sp-002',year=2027,min_sun_days=0,min_joint_days=0)
    assert res['primary_passed']
    assert len(res['recommended_backups'])==len(get_sites_catalog())-1
    assert 'NASA' in res['provenance']['annual_metrics']
def test_contingency_failing_primary():
    res=evaluate_contingency('lola-sp-003',year=2027,min_sun_days=366,min_joint_days=0)
    assert not res['primary_passed']
    assert 'Fails sunlight requirement' in res['primary_site']['explanation']
    assert res['recommended_backups']==[]
