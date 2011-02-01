#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 Loic Jaquemet loic.jaquemet+taleo@gmail.com
#



import httplib, urllib

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

def request(pageId):
  params=getParams(paramsFile)
  params[TAMPERPARAM]=pageId
  params1=['%s=%s'%(k,v) for k,v in params.items()]
  params='&'.join(params1)
  headers=getParams(headersFile,sep=':')
  # open connection
  conn = httplib.HTTPSConnection(SERVER, PORT)
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


class JobOffer():
  BADPATTERNS=['applicants must be legally authorized to work in the United States']
  prefix='jobOffer.'
  def __init__(self,idn,data):
    self.id=idn
    self.data=data
    self.interesting=None
    
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
    
  def writeToFile(self):
    fout=file(self.prefix+'%s'%self.id,'w')
    fout.write(data)
  
  def __repr__(self):
    return '<Job page %s>'%(self.id)  

import sys
jobs=[]
idn=1
conn=request(idn)
data=handleResponse(conn)
if data is None:
  print 'error'
  sys.exit()

job=JobOffer(idn,data)
if job.isInteresting():
  job.writeToFile()
  jobs.append(job)

job.writeToFile()

print jobs


