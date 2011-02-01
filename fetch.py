#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 Loic Jaquemet loic.jaquemet+taleo@gmail.com
#



import httplib, urllib,time
import lxml,lxml.html,re,os
from lxml import etree
from operator import itemgetter, attrgetter


SERVER='sas.taleo.net'
PORT=443
URL='/careersection/10000/jobdetail.ajax'
METHOD='POST'

TAMPERPARAM='rdPager.currentPage'
MAXNUM='descRequisition.nbElements'

headersFile='headers.flat'
paramsFile='example2.flat'
respFile='test.out'


def remove_html_tags(data):
    p = re.compile(r'<.*?>')
    return p.sub('', data)


def readJobOffer(dirname='ok'):
  files=[os.path.sep.join([dirname,f]) for f in os.listdir(dirname)]
  jobs=sorted([JobOffer(file(f).read()) for f in files],key=attrgetter('id'))
  return jobs


class JobsFetcher():
  def __init__(self):
    # open connection
    self.conn = httplib.HTTPSConnection(SERVER, PORT)
    self.jobs=dict()
    self._preload()
  
  def _preload(self):
    for job in readJobOffer(dirname='ok'):
      self.jobs[job.id]=job
    for job in readJobOffer(dirname='ko'):
      self.jobs[job.id]=job

  def getParams(self,filename,sep='='):
    pfile=file(filename)
    params=dict()
    for line in pfile.readlines():
      kv=line.split(sep)
      if kv[0] != 'initialHistory':
        params[kv[0]]=sep.join(kv[1:]).strip('\n')
    return params

  def printParams(self,params,sep='='):
    for k,v in params.items():
      print '%s%s%s'%(k,sep,v)

  def uncompress(self,cdata):
    import StringIO, gzip
    compressedstream = StringIO.StringIO(cdata) 
    gzipper = gzip.GzipFile(fileobj=compressedstream)
    data = gzipper.read() 
    return data

  def request(self,pageId):
    params=self.getParams(paramsFile)
    # tamper with data
    params[TAMPERPARAM]=pageId
    params1=['%s=%s'%(k,v) for k,v in params.items()]
    params='&'.join(params1)
    headers=self.getParams(headersFile,sep=':')
    # make the request
    self.conn.request(METHOD,URL,params,headers)
    print 'requested %d'%pageId
    return self.conn

  def handleResponse(self):
    resp=self.conn.getresponse()
    respC=resp.getheader('connection')
    if respC == 'close':
      print 'BAD: connection is closed.'
      print resp.reason
      print resp.getheaders()
      return None
    else:
      data=resp.read()
      if resp.getheader('content-encoding') == 'gzip':
        data=self.uncompress(data)
      return data

  def getJobOffer(self,idn):
    if idn in self.jobs:
      return self.jobs[idn]
    self.request(idn)
    data=self.handleResponse()
    if data is None:
      print 'error, reopenning connection'
      raise IOError()
    #parse it
    job=JobOffer(data)
    #cache it
    self.jobs[job.id]=job
    return job



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
    self.title=remove_html_tags(meta[101]).strip('\n')
    self.id=int(meta[71])
    self.maxOffers=int(meta[63])
  
  def __repr__(self):
    return '<Job page %s : %s>'%(self.id,self.title)  




def fetchJobOffers():
  start=1
  fetcher=JobsFetcher()
  # go
  job=fetcher.getJobOffer(start)
  #triage
  if job.isInteresting():
    job.writeToFile('ok')
  else:
    job.writeToFile('ko')

  for idn in range(start+1,job.maxOffers):
    try:
      job=fetcher.getJobOffer(idn)
    except IOError,e:
      conn=httplib.HTTPSConnection(SERVER, PORT)
      job=fetcher.getJobOffer(idn)
    #triage
    if job.isInteresting():
      job.writeToFile('ok')
    else:
      job.writeToFile('ko')


fetchJobOffers()
jobs=readJobOffer()
print ' * '+'\n * '.join([str(j) for j in jobs])


