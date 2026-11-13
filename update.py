#!/usr/bin/env python3
"""RSS -> source-linked news cards. Standard library only; no secret required."""
import datetime as dt, email.utils, hashlib, html, json, os, re, sys, urllib.request, xml.etree.ElementTree as ET
from pathlib import Path
from html.parser import HTMLParser
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'data'/'articles.json'
FEEDS=[('Google Developers','https://developers.googleblog.com/feeds/posts/default?alt=rss','Web'),('Google Japan Blog','https://japan.googleblog.com/feeds/posts/default?alt=rss','AI'),('GitHub Blog','https://github.blog/feed/','Web'),('Cloudflare Blog','https://blog.cloudflare.com/rss/','セキュリティ')]
MAX_NEW=3
class Strip(HTMLParser):
 def __init__(self):super().__init__();self.parts=[]
 def handle_data(self,s):self.parts.append(s)
def plain(s):
 p=Strip();p.feed(s or '');return re.sub(r'\s+',' ',html.unescape(' '.join(p.parts))).strip()
def get_text(item,name):
 el=item.find(name);return ''.join(el.itertext()).strip() if el is not None else ''
def get_feed(name,url,category):
 req=urllib.request.Request(url,headers={'User-Agent':'TechNoUragawa/1.0 (RSS news aggregator)'})
 with urllib.request.urlopen(req,timeout=15) as r: raw=r.read(1_500_000)
 root=ET.fromstring(raw)
 items=root.findall('.//item')
 result=[]
 for it in items[:12]:
  title=plain(get_text(it,'title'));link=get_text(it,'link').strip();description=plain(get_text(it,'description'))
  if not title or not link.startswith('https://'):continue
  try:date=email.utils.parsedate_to_datetime(get_text(it,'pubDate')).date().isoformat()
  except Exception:date=dt.date.today().isoformat()
  result.append(dict(id=int(hashlib.sha256(link.encode()).hexdigest()[:12],16),cat=category,icon={'AI':'🤖','Web':'🌐','セキュリティ':'🔐'}.get(category,'📰'),date=date,title=title[:160],desc=(description[:145]+'…' if len(description)>145 else description) or '公式サイトの発表を紹介します。',summary=(description[:550]+'…' if len(description)>550 else description) or '詳しい内容は出典の公式ページをご確認ください。',talk=['「'+title[:48]+'」っていうニュースが出てるんだね！','そうだね。ここでは配信元の見出しと概要を紹介しているよ。','具体的に何が変わるのかな？','詳しい内容や条件は、必ず出典の公式記事で確認しよう。'],source=link,sourceName=name,mode='rss'))
 return result
def main():
 old=[]
 if OUT.exists():
  try:old=json.loads(OUT.read_text('utf-8'))
  except Exception:pass
 if not isinstance(old,list):old=[]
 candidates=[];fail=[]
 for name,url,cat in FEEDS:
  try:candidates+=get_feed(name,url,cat)
  except Exception as e:fail.append(f'{name}: {e}')
 if not candidates:
  print('No feeds available; keeping existing data. '+ '; '.join(fail));return 0 if old else 1
 known={str(x.get('id')) for x in old if isinstance(x,dict)}
 candidates.sort(key=lambda x:x['date'],reverse=True)
 new=[]
 for a in candidates:
  if str(a['id']) not in known and len(new)<MAX_NEW:
   new.append(a);known.add(str(a['id']))
 combined=new+old
 combined=sorted(combined,key=lambda x:x.get('date',''),reverse=True)[:90]
 OUT.parent.mkdir(parents=True,exist_ok=True)
 data=json.dumps(combined,ensure_ascii=False,indent=2)+'\n'
 if not OUT.exists() or OUT.read_text('utf-8')!=data:OUT.write_text(data,encoding='utf-8')
 print(f'New: {len(new)}; total: {len(combined)}; feed failures: {len(fail)}')
 return 0
if __name__=='__main__':sys.exit(main())
