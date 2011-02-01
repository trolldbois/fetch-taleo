#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 Loic Jaquemet loic.jaquemet+taleo@gmail.com
#



import httplib, urllib,time
import lxml,lxml.html,re,os
from lxml import etree

SERVER='sas.taleo.net'
PORT=443
URL='/careersection/10000/jobdetail.ajax'
METHOD='POST'

TAMPERPARAM='rdPager.currentPage'
MAXNUM='descRequisition.nbElements'

headersFile='headers.flat'
paramsFile='example2.flat'
respFile='test.out'


def getParams(filename,sep='='):
  pfile=file(filename)
  params=dict()
  for line in pfile.readlines():
    kv=line.split(sep)
    if kv[0] != 'initialHistory':
      params[kv[0]]=sep.join(kv[1:]).strip('\n')
  return params

def printParams(params,sep='='):
  for k,v in params.items():
    print '%s%s%s'%(k,sep,v)

def uncompress(cdata):
  import StringIO, gzip
  compressedstream = StringIO.StringIO(cdata) 
  gzipper = gzip.GzipFile(fileobj=compressedstream)
  data = gzipper.read() 
  return data

def request(conn,pageId):
  params=getParams(paramsFile)
  params[TAMPERPARAM]=pageId
  params1=['%s=%s'%(k,v) for k,v in params.items()]
  params='&'.join(params1)
  headers=getParams(headersFile,sep=':')
  #conn = httplib.HTTPConnection('localhost', '8080')
  conn.request(METHOD,URL,params,headers)
  return conn

def handleResponse(conn):
  resp=conn.getresponse()
  respC=resp.getheader('connection')
  if respC == 'close':
    print 'BAD: connection is closed.'
    print resp.reason
    print resp.getheaders()
    return None
  else:
    data=resp.read()
    if resp.getheader('content-encoding') == 'gzip':
      data=uncompress(data)
    return data

def remove_html_tags(data):
    p = re.compile(r'<.*?>')
    return p.sub('', data)

class JobOffer():
  BADPATTERNS=['applicants must be legally authorized to work in the United States']
  prefix='jobOffer.'
  def __init__(self,data):
    self.data=data
    self.interesting=None
    self.parse()
    
  def isInteresting(self):
    #caching
    if self.interesting is not None:
      return self.interesting
    # searching
    for p in self.BADPATTERNS:
      if p in self.data:
        self.interesting = False
        return self.interesting
      pass
    # true....
    self.interesting = True
    return  self.interesting
    
  def writeToFile(self,dirname='./'):
    fout=file(os.path.sep.join([dirname,self.prefix+'%s'%self.id]),'w')
    fout.write(self.data)

  def parse(self):
    #f='jobOffer.1'
    #tree= lxml.html.parse(f)
    #root=tree.getroot()
    root=lxml.html.fromstring(self.data)
    response=root.get_element_by_id('response')
    meta=etree.tostring(response, pretty_print=True, method="html").split('!|!')
    self.title=remove_html_tags(meta[101])
    self.id=meta[71]
    self.maxOffers=int(meta[63])
  
  def __repr__(self):
    return '<Job page %s : %s>'%(self.id,self.title)  


def getJobOffer(conn,idn):
  conn=request(conn,idn)
  data=handleResponse(conn)
  if data is None:
    print 'error'
    sys.exit()
  #parse it
  job=JobOffer(data)
  return job

import sys
jobs=[]
idn=1
# open connection
conn = httplib.HTTPSConnection(SERVER, PORT)

job=getJobOffer(conn,idn)
if job.isInteresting():
  job.writeToFile('ok')
  jobs.append(job)
else:
  job.writeToFile('ko')

for idn in range(2,job.maxOffers):
  job=getJobOffer(conn,idn)
  if job.isInteresting():
    job.writeToFile('ok')
    jobs.append(job)
  else:
    job.writeToFile('ko')
  
  time.sleep(0.5)

print jobs


