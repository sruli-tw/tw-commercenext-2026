#!/usr/bin/env python3
"""CommerceNext bulk microsite builder (CI).
Reads tools/contacts_compact.tsv (no emails / no firmographics) + the live gh-pages
checkout (./live with shared/app.js, hub2.js, style.css, data.json incl. 8 pilot pages),
writes the full static site to ./out. Design is LOCKED; all variation is data + copy.
"""
import csv, json, re, os, hashlib, shutil, sys

LIVE, OUT = sys.argv[1] if len(sys.argv)>1 else 'live', sys.argv[2] if len(sys.argv)>2 else 'out'
BASE_URL = 'https://sruli-tw.github.io/tw-commercenext-2026/'
OG_IMG = 'https://storage.googleapis.com/ai-moby-shofifi/shops/acct_1GPwMuAQRPl2PkoW/sessions/moby_dgm1b9ez6vcq/images/og_banner_commercenext_v3.png'

CHIPS20 = ['Site optimization & PDP improvements','Customer experience & post-purchase','Content marketing & SEO',
 'Retention & loyalty marketing','Digital advertising & measurement','Product discovery & personalization',
 'Advertising creative','Affiliate, influencer & social commerce','Checkout optimization',
 'Emerging channels (CTV, podcasts, DOOH)','Retail media','Emerging tech (AR/VR, live & immersive)',
 'International expansion','Operations & fulfillment','Payments (mobile, BNPL)','Agentic AI & workflow automation',
 'Predictive & generative AI','Data & analytics','Social commerce & live shopping','Marketplaces & third-party platforms']
CATS = {'A':('an apparel and footwear business','seasonal drops, deep catalogs, and paid channels that all claim the same sale make clean measurement genuinely hard'),
 'B':('a beauty brand','repeat purchase and channel-saturated paid media make the gap between platform-reported and real performance expensive'),
 'F':('a food and CPG business','thin margins mean every marketing dollar has to be defended with measurement, not platform claims'),
 'H':('a home and furniture brand','long consideration cycles make click-based attribution systematically misleading'),
 'W':('a health and wellness business','subscription behavior and first-party data discipline are the foundation of growth'),
 'J':('a considered-purchase brand','customers research for weeks and last-click numbers undercredit everything that starts the journey'),
 'E':('a consumer electronics business','high order values and multi-channel retail make channel-reported ROAS especially unreliable'),
 'T':('a brand in a gift-heavy category','seasonal peaks compress a year of measurement mistakes into a few weeks'),
 'S':('an enthusiast-category brand','a passionate, returning customer base makes lifecycle measurement pay off fastest'),
 'P':('a pet brand','replenishment behavior rewards teams that see retention next to acquisition'),
 'G':('a gifting business','demand spikes around moments and measurement has to keep up in days, not quarters'),
 'D':('a large multi-category retailer','the volume of signals across categories outruns what any team can read manually'),
 'X':('an ecommerce business','the volume of daily signals across channels outruns what any team can read manually'),
 '':('an ecommerce business','the volume of daily signals across channels outruns what any team can read manually')}
def seed(s, n): return int(hashlib.md5(s.encode()).hexdigest(),16) % n
def slugify(s): return re.sub(r'[^a-z0-9]+','-', (s or '').lower()).strip('-')
low = lambda s: s[0].lower()+s[1:] if s and not s.isupper() and not s[0:2].isupper() else s

def persona_of(title, chips, sen):
    t = ' '+ (title or '').lower() + ' '
    has = lambda *ks: any(k in t for k in ks)
    if has('retention','crm','lifecycle','loyalty','email marketing',' email','sms'): return 'Retention / CRM'
    if has('cmo','chief marketing','chief brand','chief growth','chief revenue','chief customer'): return 'Executive / Growth'
    if has('ceo','founder','co-founder','cofounder','owner','president','coo ','chief','cdo','cto','cio',' gm ','general manager','managing director','board','principal','chief of staff','cfo','partner '): return 'Executive / Operator'
    if has('performance','paid media','paid social','paid search','media buy','acquisition','advertis','ppc',' sem ','demand gen','google ads','media manager','media director',' media '): return 'Growth / Performance'
    if has(' vp','vice president','svp','evp','head of','director') and has('marketing','growth','revenue','sales & marketing','sales and marketing'): return 'Executive / Growth'
    if has('brand','creative','content','social media','influencer','communic','copy'): return 'Brand / Creative + AI'
    if has('ecom','e-com','digital','website','web ','site ','marketplace','amazon','merchandis','omni','product','innovation','technology','martech','cx','customer experience','online','internet','eshop','e-shop','growth'): return 'Ecommerce / Digital'
    if has('data','analytic','insight','intelligence','research'): return 'Data / Analytics'
    if has('marketing'): return 'Executive / Growth' if sen in ('V','C') else 'Growth / Performance'
    if chips:
        c0=chips[0]
        if 'Retention' in c0: return 'Retention / CRM'
        if 'Digital advertising' in c0 or 'creative' in c0.lower(): return 'Growth / Performance'
        if 'AI' in c0: return 'Executive / Operator'
    return 'Ecommerce / Digital'

WF = {
 'spend_brief':("Morning spend-quality brief","Moby monitors every channel's spend, efficiency, and trend against your targets overnight.","It drafts scale / hold / cut recommendations with the reasoning attached \u2014 grounded in attribution, not platform-reported numbers.","You approve every budget move; nothing changes without sign-off."),
 'creative_fatigue':("Creative fatigue early warning","Moby watches frequency, CTR decay, and efficiency by creative across paid social.","It flags fatigue before performance falls off a cliff and drafts what to rotate in.","Your team approves rotations and keeps creative control."),
 'channel_mix':("Channel mix truth, including the hard channels","MMM and incrementality testing read CTV, podcasts, retail media, and affiliates on equal footing with paid social and search.","Moby drafts the mix recommendation in plain English.","You approve reallocations \u2014 with evidence you can defend upward."),
 'retail_media':("Retail media accountability","Moby watches marketplace and retail media performance against blended business results.","It drafts a plain-English read on what retail media is truly adding versus capturing.","You approve budget shifts between retail media and direct channels."),
 'lifecycle_watch':("Lifecycle revenue watch","Moby monitors repeat rate, time-to-second-purchase, and revenue by segment and flow.","It drafts a weekly digest: which flows and segments are gaining or fading, and why.","You approve any changes to flows or campaigns \u2014 Moby never sends on its own."),
 'segment_drafting':("Segment and flow drafting","Moby watches for segments worth acting on \u2014 lapsing high-value buyers, first-time buyers in a key category, replenishment windows coming due.","It drafts the segment definition, the offer logic, and the campaign concept.","You review, edit, and approve before anything goes live in your ESP."),
 'campaign_explained':("Campaign performance, explained","Custom dashboards track every send's revenue contribution beyond opens and clicks.","Moby drafts the plain-English readout \u2014 what beat expectations, what underperformed, and the next test to run.","You approve the test plan and keep full control of the calendar."),
 'site_funnel':("Site funnel watch","Moby monitors conversion rate, PDP engagement, and checkout completion by landing path and device.","When something breaks trend \u2014 a template change, a slow page, a path that stops converting \u2014 it drafts the diagnosis.","You approve the fix priority; nothing is changed for you."),
 'landing_paths':("Landing path & campaign alignment","Moby watches which ad-to-page paths convert and which burn spend.","It drafts recommendations: which pages deserve more traffic, which need work before more spend goes to them.","You and the marketing team approve changes together \u2014 from one shared set of numbers."),
 'dtc_view':("One DTC operating view","Custom dashboards combine acquisition, site, and retention into the view your weekly meeting actually needs.","Moby drafts the weekly readout and flags exceptions before they become problems.","You approve actions; the data work is already done."),
 'business_pulse':("Daily business pulse, written for the operator","Moby monitors revenue, spend, contribution, and conversion across channels every morning.","It drafts a short plain-English brief: what changed, why it likely changed, and what's worth a decision today.","Your team approves any follow-up action \u2014 nothing moves without sign-off."),
 'anomaly':("Anomaly detection with explanations, not alerts","Moby watches for breaks in trend \u2014 a channel's efficiency dropping, a category stalling, a margin shift.","Instead of a red number, it drafts the explanation and a recommended response.","You or the owning lead approves the response before anything is executed."),
 'operating_layer':("One operating layer across growth, retention, and finance","Custom dashboards unify paid media, retention, site, and P&L views so every team argues from the same numbers.","Moby drafts the weekly operating review against those views \u2014 the prep work, done before the meeting.","Leadership keeps the decisions; Moby keeps the legwork."),
 'commercial_brief':("Weekly commercial brief","Moby monitors spend, revenue, and efficiency across every channel you own.","It drafts a one-page operating brief: what's working, what's drifting, and recommended moves with expected impact.","You approve the moves; your team executes with the analysis already done."),
 'demand_quality':("Demand quality by source","Moby connects each acquisition source to order value and repeat behavior.","It drafts a quarterly view of which sources bring the best customers.","You approve where the next dollar goes."),
 'creative_loop':("Creative learning loop","Moby monitors creative performance across channels \u2014 fatigue, hook performance, which concepts hold efficiency at scale.","It drafts a weekly creative readout: which angles deserve more budget, which are decaying, and a brief for the next round of concepts.","Your team approves the brief and any budget shift behind it."),
 'content_commerce':("Content-to-commerce reporting","Custom dashboards connect content, social, and influencer activity to revenue and customer quality.","Moby drafts the monthly story for leadership \u2014 what worked, what to repeat, what to retire.","You approve and present it; the analysis hours come back to your team."),
 'discovery':("Discovery & personalization proof","Moby watches on-site search, PDP engagement, and discovery paths against revenue per session.","It drafts which discovery improvements actually paid for themselves \u2014 in revenue, not engagement metrics.","You approve the roadmap order."),
 'intl_watch':("International expansion scoreboard","Moby monitors performance by market \u2014 acquisition efficiency, conversion, and customer quality side by side.","It drafts a per-market read: where to lean in, where to fix the funnel before adding spend.","You approve market-level budget decisions."),
 'ai_governance':("Agentic AI with a governance answer","Moby monitors the signals you assign it \u2014 spend, funnel, retention \u2014 on top of measurement you can audit.","Every output is a draft: a recommendation with the reasoning shown, never a silent change.","You approve each action. That's the contract \u2014 monitors, drafts, approval."),
 'data_unify':("One consistent data layer","Your data is unified in a managed, AI-optimized warehouse with 60+ one-click integrations \u2014 no engineering project.","Moby drafts answers to ad-hoc questions in minutes against that layer, instead of an analyst queue.","You approve what becomes a standing dashboard or report."),
}
CHIP_WF = {4:'spend_brief',6:'creative_fatigue',9:'channel_mix',10:'retail_media',19:'retail_media',3:'lifecycle_watch',
 1:'segment_drafting',0:'site_funnel',8:'site_funnel',5:'discovery',15:'ai_governance',16:'ai_governance',
 17:'data_unify',12:'intl_watch',2:'content_commerce',7:'content_commerce',18:'content_commerce'}
P_WF = {'Executive / Operator':['business_pulse','anomaly','operating_layer'],
 'Executive / Growth':['commercial_brief','channel_mix','demand_quality'],
 'Growth / Performance':['spend_brief','creative_fatigue','channel_mix'],
 'Brand / Creative + AI':['creative_loop','channel_mix','content_commerce'],
 'Retention / CRM':['lifecycle_watch','segment_drafting','campaign_explained'],
 'Ecommerce / Digital':['site_funnel','landing_paths','dtc_view'],
 'Data / Analytics':['data_unify','anomaly','business_pulse']}
def workflows_for(persona, idxs):
    keys = list(P_WF[persona]); cand = [CHIP_WF[i] for i in idxs if i in CHIP_WF]
    si = 1
    for k in cand:
        if k not in keys and si < 3: keys[si] = k; si += 1
    out=[]; seen=set()
    for k in keys:
        if k not in seen: seen.add(k); out.append({'t':WF[k][0],'m':WF[k][1],'d':WF[k][2],'a':WF[k][3]})
    i=0; fillers = P_WF[persona]+['anomaly','dtc_view','data_unify']
    while len(out)<3:
        k=fillers[i]; i+=1
        if k not in seen: seen.add(k); out.append({'t':WF[k][0],'m':WF[k][1],'d':WF[k][2],'a':WF[k][3]})
    return out[:3]
P_THESIS = {
 'Executive / Operator':["That is exactly the question Triple Whale was built to answer: not \u201ccan AI chat about my data,\u201d but \u201ccan AI reliably do the daily work \u2014 on top of measurement we trust?\u201d","Moby is built around a governance contract leadership can live with: it monitors, it explains, it drafts \u2014 and your team approves every action."],
 'Executive / Growth':["Triple Whale gives you one measurement layer across all of it, and Moby turns that into a weekly operating rhythm rather than a quarterly reporting scramble.","With MTA, MMM, and incrementality in one place, you get a single defensible read on every channel \u2014 and an AI teammate that drafts the decisions, with you keeping sign-off."],
 'Growth / Performance':["That is exactly where Triple Whale's combination of MTA, MMM, and incrementality earns its keep: one trustworthy read across channels that all claim the same conversion.","Triple Whale grounds those calls in attribution you can trust, and Moby turns the daily \u201cwhat do we do by 10am\u201d into drafted scale / hold / cut recommendations you approve."],
 'Brand / Creative + AI':["That pairing is exactly where Triple Whale + Moby is strongest: knowing which stories and angles actually earn more support, then having an AI teammate do the analysis work to prove it.","Triple Whale connects creative and content to revenue \u2014 not just engagement \u2014 and Moby drafts the readouts and briefs so the analysis hours come back to your team."],
 'Retention / CRM':["Triple Whale brings retention and lifecycle data into the same measurement layer as everything else, and Moby acts like an extra analyst on your lifecycle team: watching segments, drafting ideas, and never sending anything without your approval.","When lifecycle revenue sits next to paid and site data, you can prove retention's contribution instead of asserting it \u2014 and Moby does the watching and drafting daily."],
 'Ecommerce / Digital':["Triple Whale connects traffic, site behavior, and revenue in one place, and Moby watches the funnel daily so you don't have to spot every break manually.","One measurement layer across acquisition, site, and retention ends the \u201cad problem or site problem?\u201d debate quickly \u2014 and Moby drafts the diagnosis when something breaks trend."],
 'Data / Analytics':["Triple Whale unifies your stack in a managed, AI-optimized warehouse \u2014 and Moby answers the ad-hoc questions in minutes so the analyst queue stops being the bottleneck.","One consistent data layer plus an AI teammate that shows its reasoning: faster answers, same rigor, your sign-off on anything that changes."],
}
P_HOOK = {
 'Executive / Operator':["Maxx co-founded Triple Whale after running an ecommerce business himself \u2014 his session on turning first-party data into profit is told from the operator's seat.","Maxx's session is about turning first-party data into profit with AI-powered CX \u2014 the same build-vs-buy question most leadership teams are working through on agentic AI."],
 'Executive / Growth':["Maxx ran an ecommerce business before co-founding Triple Whale \u2014 his session on first-party data and profit is built for operators who own the whole number, not just one channel.","Maxx's 9:35am session connects first-party data to profit \u2014 the measurement half of your remit; the booth conversation can cover the action half."],
 'Growth / Performance':["Maxx's session on turning first-party data into profit speaks directly to the measurement half of your profile \u2014 and the booth conversation can cover the action half.","Maxx's 9:35am session on first-party data and profit is a strong warm-up for exactly this conversation \u2014 then the booth demo can be about your channels specifically."],
 'Brand / Creative + AI':["Maxx's session covers turning first-party data into profit \u2014 including how creative and CX signals become decisions, which sits exactly at your remit.","Maxx's session is about AI-powered CX from first-party data \u2014 the proof layer behind every creative bet your team makes."],
 'Retention / CRM':["Maxx's session is literally about turning first-party data into profit through CX \u2014 first-party data is the raw material of your entire lifecycle program.","Maxx's 9:35am session on first-party data and profit maps directly to lifecycle work: the data is yours; the profit is the retention curve."],
 'Ecommerce / Digital':["Maxx's session is about AI-powered CX from first-party data \u2014 the site is where that CX actually happens, and the examples are directly portable to your roadmap.","Maxx's session on turning first-party data into profit through CX maps directly to your site and digital priorities."],
 'Data / Analytics':["Maxx's session on turning first-party data into profit is, at its core, a data architecture story \u2014 told for operators rather than engineers.","Maxx's 9:35am session makes the case that trusted first-party measurement is the foundation everything else compounds on \u2014 your thesis, on a main stage."],
}
P_TENSION = {'Executive / Operator':'the gap between what the data says and what the team does next',
 'Executive / Growth':'knowing which of your channels is actually producing',
 'Growth / Performance':'getting one trustworthy read across channels that all claim the same conversion',
 'Brand / Creative + AI':'proving which creative bets actually earn more support',
 'Retention / CRM':"proving retention's contribution instead of asserting it",
 'Ecommerce / Digital':'reconciling \u201ctraffic looked great\u201d with \u201crevenue didn\u2019t move\u201d',
 'Data / Analytics':'getting every team to argue from the same numbers'}
def build_why(comp, title, catc, chips, persona, slug):
    catdesc, tension = CATS[catc]
    s1 = ["For {} like {}, {}.".format(catdesc, comp, tension), "{} operates as {} \u2014 a business where {}.".format(comp, catdesc, tension)][seed(slug,2)]
    if chips:
        pr = low(chips[0]) + (' and ' + low(chips[1]) if len(chips)>1 else '')
        s2 = ["Your event profile leads with {}, which tells us where the conversation should start.".format(pr),
              "Your event profile points at {} \u2014 so that's what this page is built around.".format(pr)][seed(slug+'x',2)]
    else:
        s2 = "Based on your role as {}, the daily question is {}.".format(title, P_TENSION[persona])
    return "{} {} {}".format(s1, s2, P_THESIS[persona][seed(slug+'y',2)])
P_PTS = {
 'Executive / Operator':["At the leadership level, the bottleneck isn't dashboards \u2014 it's the gap between what the data says and what the team does next. An AI layer is only as good as the measurement underneath it.","Channel-reported numbers disagree by design. MTA, MMM, and incrementality give you one defensible version of the truth to operate from.","Agentic AI evaluated at the executive level needs a governance answer: what does it monitor, what does it draft, and who approves. Moby is built around exactly that contract."],
 'Executive / Growth':["When every channel reports its own ROAS, the sum is always more revenue than you actually made. Blended measurement with MMM separates real contribution from noise.","Budget conversations need decisions framed for approval \u2014 current state, recommendation, expected impact \u2014 not raw dashboards.","Customer quality belongs in the acquisition conversation: which sources bring buyers who come back, not just the cheapest first order."],
 'Growth / Performance':["When six channels each report their own ROAS, the sum is always more revenue than you actually made. First-party attribution plus MMM resolves the double-counting.","The real workflow question isn't \u201cwhat happened\u201d but \u201cwhat do we do by 10am\u201d \u2014 scale, hold, or cut, with the reasoning written down.","Creative is the scaling lever; knowing which angles fatigue and which hold up is the difference between scaling and plateauing."],
 'Brand / Creative + AI':["Creative decisions without attribution become taste debates. MTA plus incrementality shows which angles, hooks, and formats drive real revenue \u2014 not just platform-reported wins.","Content and social deserve a revenue answer, not a reach answer \u2014 one layer connecting creative work to customer quality settles it.","Agentic AI for a brand team shouldn't mean a black box making changes. It should mean drafts, briefs, and recommendations that a human approves."],
 'Retention / CRM':["Email and SMS performance only makes sense next to the rest of the business. When lifecycle revenue sits in the same view as paid and site data, you can prove retention's contribution instead of asserting it.","Segmentation is where lifecycle programs win or stall. Customer-level data \u2014 repeat rates, time between orders, product affinities \u2014 should drive who gets which message.","Post-purchase experience is a retention lever. Measuring it alongside lifecycle revenue shows which fixes actually move second-purchase rate."],
 'Ecommerce / Digital':["You own the surface where every marketing dollar either converts or doesn't \u2014 landing-path and funnel views show where intent leaks out.","Site and discovery improvements deserve revenue-based measurement \u2014 not just engagement metrics \u2014 so you can prove which changes paid for themselves.","When paid traffic underperforms, the question is always \u201cad problem or site problem?\u201d Having both in one measurement layer ends that debate quickly."],
 'Data / Analytics':["Every team arguing from its own export is how the same meeting happens three times. One managed data layer ends that.","AI answers are only as good as the data contract underneath \u2014 measurement you can audit beats a clever summary of numbers you can't.","The win isn't fewer dashboards; it's fewer hours between a good question and a defensible answer."],
}
def build_pts(persona, idxs, catc):
    pts = list(P_PTS[persona])
    if persona in ('Growth / Performance','Executive / Growth','Ecommerce / Digital') and catc:
        cd, tn = CATS[catc]
        pts[0] = "For {}, {} \u2014 which is exactly the problem first-party attribution plus MMM was built to fix.".format(cd, tn)
    s = set(idxs)
    if 10 in s and persona!='Retention / CRM':
        pts[1] = "Retail media (Amazon and beyond) deserves the same scrutiny as paid social \u2014 incrementality answers whether it's driving new demand or taxing demand you already had."
    if 9 in s:
        pts[1] = "Emerging channels like CTV and podcasts are where last-click measurement fails hardest. MMM gives you a defensible read on channels that don't produce a clean click."
    if 12 in s:
        pts[2] = "International expansion multiplies the measurement problem by every new market \u2014 one consistent layer across markets is the difference between scaling a playbook and rediscovering it."
    return pts
FIT_FALLBACK = {'Executive / Operator':'Trusted measurement + governed AI','Executive / Growth':'Channel truth + operating rhythm',
 'Growth / Performance':'Attribution you can trust + daily drafts','Brand / Creative + AI':'Creative proof + AI legwork',
 'Retention / CRM':'Lifecycle measurement + drafted campaigns','Ecommerce / Digital':'Funnel truth + a watchful teammate',
 'Data / Analytics':'One data layer + fast answers'}

def og_shell(slug, comp, name):
    t = "{} \u00d7 Triple Whale \u2014 CommerceNext NYC".format(comp)
    d = "A short operating concept prepared for {} ahead of CommerceNext \u2014 plus Maxx Blank's session (Wed 9:35 AM) and Booth 366.".format(name)
    e = lambda x: x.replace('&','&amp;').replace('"','&quot;')
    return ('<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Triple Whale \u00d7 CommerceNext</title>\n'
     '<meta property="og:type" content="website">\n<meta property="og:title" content="'+e(t)+'">\n<meta property="og:description" content="'+e(d)+'">\n'
     '<meta property="og:image" content="'+OG_IMG+'">\n<meta property="og:image:width" content="1200">\n<meta property="og:image:height" content="630">\n'
     '<meta property="og:url" content="'+BASE_URL+slug+'/">\n<meta name="twitter:card" content="summary_large_image">\n'
     '<meta name="twitter:title" content="'+e(t)+'">\n<meta name="twitter:description" content="'+e(d)+'">\n<meta name="twitter:image" content="'+OG_IMG+'">\n'
     '<link rel="stylesheet" href="../shared/style.css"></head>'
     '<body data-slug="'+slug+'"><script src="../shared/app.js"></script></body></html>')

def main():
    here = os.path.dirname(os.path.abspath(__file__))
    pilot = json.load(open(os.path.join(LIVE,'shared','data.json')))
    appjs = open(os.path.join(LIVE,'shared','app.js')).read()
    contacts, order = {}, []
    used = set(pilot['contacts'].keys())
    for line in open(os.path.join(here,'contacts_compact.tsv')):
        line=line.rstrip('\n')
        if not line: continue
        name,title,comp,dom,catc,sen,ch = line.split('\t')
        idxs = [int(x) for x in ch.split('.') if x!='']
        chips = [CHIPS20[i] for i in idxs]
        persona = persona_of(title, chips, sen)
        s = slugify(name) + '-' + slugify(comp.split('(')[0])[:24].strip('-')
        b=s; i=2
        while s in used: s = "{}-{}".format(b,i); i+=1
        used.add(s)
        entry = {'company':comp,'name':name,'title':title,'persona':persona,
            'fit': (chips[0]+' + '+low(chips[1])) if len(chips)>=2 else (chips[0] if chips else FIT_FALLBACK[persona]),
            'chips': chips if chips else ['Measurement you can trust','Moby AI teammates','Approval-first workflows'],
            'why': build_why(comp,title,catc,chips,persona,s),
            'pts': build_pts(persona, idxs, catc),
            'wf': workflows_for(persona, idxs),
            'hook': P_HOOK[persona][seed(s+'h',2)], 'domain': dom}
        if not chips: entry['h2'] = "Built around your seat at {}".format(comp)
        contacts[s]=entry; order.append(s)
    merged = {'contacts': dict(list(pilot['contacts'].items()) + list(contacts.items())),
              'order': pilot['order'] + sorted(order, key=lambda s: contacts[s]['company'].lower())}
    old = '<h2>Built around the priorities in your event profile</h2>'
    if old in appjs:
        appjs = appjs.replace(old, '<h2>{{WHYH2}}</h2>').replace(
          "CHIPS:chips,WHY:c.why", "CHIPS:chips,WHY:c.why,WHYH2:(c.h2||'Built around the priorities in your event profile')")
        assert '{{WHYH2}}' in appjs and 'c.h2||' in appjs
    # assemble out: start from live (pilot folders, README), overlay
    if os.path.exists(OUT): shutil.rmtree(OUT)
    shutil.copytree(LIVE, OUT, ignore=shutil.ignore_patterns('.git'))
    open(os.path.join(OUT,'shared','data.json'),'w').write(json.dumps(merged, ensure_ascii=False))
    open(os.path.join(OUT,'shared','app.js'),'w').write(appjs)
    # hub root index: ensure hub2.js is loaded
    idx = open(os.path.join(OUT,'index.html')).read()
    if 'hub2.js' not in idx:
        idx = idx.replace('<script src="shared/app.js"></script>', '<script src="shared/app.js"></script><script src="shared/hub2.js"></script>')
        open(os.path.join(OUT,'index.html'),'w').write(idx)
    for s in order:
        os.makedirs(os.path.join(OUT,s), exist_ok=True)
        open(os.path.join(OUT,s,'index.html'),'w').write(og_shell(s, contacts[s]['company'], contacts[s]['name']))
    # QA
    blob = json.dumps(merged, ensure_ascii=False).lower()
    banned = ['apollo','dossier','spend band','revenue band','$100,000/mo','$500,000/mo','million to','existing partner','our partner','current partner','meddpicc']
    bad = [b for b in banned if b in blob]
    assert not bad, bad
    print('built', len(order), 'new pages; total contacts', len(merged['contacts']))
if __name__ == '__main__':
    main()
