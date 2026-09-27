#!/usr/bin/env python3
"""Preview an Identity Platform MFA configuration; --apply explicitly changes the named project.
Requires Identity Platform already enabled. No cloud calls or credentials are used in preview.
SMS regions are an operator choice; configuring them can affect all users of this project.
"""
import argparse
import copy
import json
import re

MASK = 'mfa,authorizedDomains,smsRegionConfig,signIn.email.enabled,signIn.email.passwordRequired'

def plan(existing, domains, regions, adjacent=1):
    if not domains or any(not re.fullmatch(r'[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?',d) for d in domains):
        raise ValueError('Supply exact authorized hostnames, not URLs or wildcards.')
    if not regions or any(not re.fullmatch(r'[A-Z]{2}',r) for r in regions):
        raise ValueError('Explicit SMS country/region codes are required.')
    if not 0 <= adjacent <= 2:
        raise ValueError('Reviewed starter policy accepts 0–2 adjacent TOTP intervals.')
    mfa=copy.deepcopy(existing.get('mfa',{}))
    mfa['state']='MANDATORY' if mfa.get('state')=='MANDATORY' else 'ENABLED'
    mfa['enabledProviders']=sorted(set(mfa.get('enabledProviders',[]))|{'PHONE_SMS'})
    mfa['providerConfigs']=[p for p in mfa.get('providerConfigs',[]) if 'totpProviderConfig' not in p]+[
        {'state':'ENABLED','totpProviderConfig':{'adjacentIntervals':adjacent}}]
    return {'mfa':mfa,'authorizedDomains':sorted(set(existing.get('authorizedDomains',[]))|set(domains)),
      'smsRegionConfig':{'allowlistOnly':{'allowedRegions':sorted(set(regions))}},
      'signIn':{'email':{'enabled':True,'passwordRequired':True}}}

def verify(actual, expected):
    if actual.get('mfa',{}).get('state') not in {'ENABLED','MANDATORY'}:
        raise RuntimeError('MFA is not enabled.')
    if 'PHONE_SMS' not in actual.get('mfa',{}).get('enabledProviders',[]):
        raise RuntimeError('SMS second factor is not enabled.')
    if not any(x.get('state')=='ENABLED' and x.get('totpProviderConfig')==expected['mfa']['providerConfigs'][-1]['totpProviderConfig'] for x in actual.get('mfa',{}).get('providerConfigs',[])):
        raise RuntimeError('TOTP configuration did not match.')
    if not set(expected['authorizedDomains']) <= set(actual.get('authorizedDomains',[])):
        raise RuntimeError('An authorized domain is missing.')
    if actual.get('smsRegionConfig') != expected['smsRegionConfig']:
        raise RuntimeError('SMS region policy did not match.')
    if any(actual.get('signIn',{}).get('email',{}).get(k) != v for k,v in expected['signIn']['email'].items()):
        raise RuntimeError('Email/password configuration did not match.')

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--project',required=True);p.add_argument('--domain',action='append',required=True)
    p.add_argument('--sms-region',action='append',required=True);p.add_argument('--adjacent-intervals',type=int,default=1)
    p.add_argument('--apply',action='store_true');p.add_argument('--acknowledge-project-wide-change',action='store_true')
    a=p.parse_args()
    if not re.fullmatch(r'[a-z][a-z0-9-]{4,28}[a-z0-9]',a.project):p.error('Invalid GCP project ID.')
    if a.apply and not a.acknowledge_project_wide_change:p.error('Apply requires explicit project-wide change acknowledgment.')
    body=plan({},a.domain,a.sms_region,a.adjacent_intervals)
    if not a.apply:
        print(json.dumps({'mode':'preview_only','project':a.project,'updateMask':MASK,'body':body,
            'note':'Existing authorized domains/providers will be preserved after a fresh read during apply. Tenant configuration is separate.'},indent=2));return
    import google.auth
    from google.auth.transport.requests import AuthorizedSession
    credentials,_=google.auth.default(scopes=['https://www.googleapis.com/auth/cloud-platform'])
    url=f'https://identitytoolkit.googleapis.com/admin/v2/projects/{a.project}/config'
    with AuthorizedSession(credentials) as session:
        current=session.get(url,timeout=30);current.raise_for_status()
        body=plan(current.json(),a.domain,a.sms_region,a.adjacent_intervals)
        result=session.patch(url,params={'updateMask':MASK},json=body,timeout=30);result.raise_for_status()
        after=session.get(url,timeout=30);after.raise_for_status();verify(after.json(),body)
    print(json.dumps({'project':a.project,'result':'configuration_verified','application_enforcement':'mandatory_backend_MFA'}))
if __name__=='__main__':main()
