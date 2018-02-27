# from https://github.com/kenneth59715/nsg-rest-client/blob/master/nsg.nopassword.ipynb
# This worked with python 3, with requests module installed
# use port 8443 for production, 8444 for test
# register at https://www.nsgportal.org/reg/reg.php for username and password
CRA_USER = 'changeme'
PASSWORD = 'changeme'
# for development version:
# log in at https://nsgr.sdsc.edu:8444/restusers/login.action
# for production version:
# log in at https://nsgr.sdsc.edu:8443/restusers/login.action
# Tool names can be found at Developer->Documentation (Tools: How to Configure Specific Tools)
# create a new application at Developer->Application Management (Create New Application)
# save the Application Key for use in REST requests
KEY = 'test1-D96E308858BB418CB50B5307391616BD'
# for development version:
# URL = 'https://nsgr.sdsc.edu:8444/cipresrest/v1'
# for production version:
URL = 'https://nsgr.sdsc.edu:8443/cipresrest/v1'
TOOL = 'NEURON73_TG'

import os
import requests
import xml.etree.ElementTree
import time
import sys

os.popen('pwd').read()
os.popen('ls -ltr').read()
headers = {'cipres-appkey' : KEY}
payload = {'tool' : TOOL, 'metadata.statusEmail' : 'true', 'vparam.number_cores_' : 24, 'vparam.number_nodes_' : 2, 'vparam.runtime_' : 0.5, 'vparam.filename_': 'Batch.hoc', 'vparam.cmdlineopts_': '-c TSTOP=1'}
files = {'input.infile_' : open('/media/john/scigap/nsgtest/JonesEtAl2009_r31.zip','rb')}

r = requests.post('{}/job/{}'.format(URL, CRA_USER), auth=(CRA_USER, PASSWORD), data=payload, headers=headers, files=files)
#print(r.text)

root = xml.etree.ElementTree.fromstring(r.text)

sys.stderr.write("%s\n" % r.text)
sys.stderr.write("%s\n" % r.url)

for child in root:
    if child.tag == 'resultsUri':
        for urlchild in child:
            if urlchild.tag == 'url':
                outputuri = urlchild.text
    if child.tag == 'selfUri':
        for urlchild in child:
            if urlchild.tag == 'url':
                selfuri = urlchild.text
#print(outputuri,file=sys.stderr)
sys.stderr.write("%s\n" % outputuri)
#print(selfuri,file=sys.stderr)
sys.stderr.write("%s\n" % selfuri)

headers = {'cipres-appkey' : KEY}

#print('Waiting for job to complete',file=sys.stderr)
sys.stderr.write('Waiting for job to complete\n')
jobdone = 0
while jobdone == 0:
    r = requests.get(selfuri, auth=(CRA_USER, PASSWORD), headers=headers)
    #print(r.text)
    root = xml.etree.ElementTree.fromstring(r.text)
    for child in root:
        if child.tag == 'terminalStage':
            jobstatus = child.text
            if jobstatus == 'false':
                time.sleep(5)
                #print('.',file=sys.stderr,end='')
                sys.stderr.write('.')
            else:
                jobdone = 1
                #print('',file=sys.stderr,end='\n')
                sys.stderr.write('\n')
                break

#print('Job completion detected, getting download URIs...',file=sys.stderr)
sys.stderr.write('Job completion detected, getting download URIs...')
r = requests.get(outputuri,
                 headers= headers, auth=(CRA_USER, PASSWORD))
#print(r.text)
globaldownloadurilist = []
root = xml.etree.ElementTree.fromstring(r.text)
for child in root:
    if child.tag == 'jobfiles':
        for jobchild in child:
            if jobchild.tag == 'jobfile':
                for downloadchild in jobchild:
                    if downloadchild.tag == 'downloadUri':
                        for attchild in downloadchild:
                            if attchild.tag == 'url':
                                #print(attchild.text)
                                sys.stdout.write(attchild.text)
                                globaldownloadurilist.append(attchild.text)
                
#print('Download complete.  Run the next cell.',file=sys.stderr)
sys.stderr.write('Download complete.  Run the next cell.\n')

#submitoutput.show()
#print(submitoutput.stdout)
#print(globaldownloadurilist)
globaloutputdict = {}
for downloaduri in globaldownloadurilist:
    r = requests.get(downloaduri, auth=(CRA_USER, PASSWORD), headers=headers)
    #print(r.text)
    globaloutputdict[downloaduri] = r.text
for name in globaloutputdict.keys():
    #continue_var = raw_input("display %s [Y/y]? " % name)
    if sys.version_info[0] < 3:
        continue_var = raw_input("display %s [Y/y]?" % name)
    else:
        continue_var = input("display %s [Y/y]?" % name)
    if continue_var in ['Y','y']:
         #print(globaloutputdict[name])
         sys.stdout.write("%s\n" % globaloutputdict[name])

#http://stackoverflow.com/questions/31804799/how-to-get-pdf-filename-with-python-requests
#downloaduri = 'https://nsgr.sdsc.edu:8443/cipresrest/v1/job/kenneth/NGBW-JOB-NEURON73_TG-650AAA3A8044475580739C88BDF7771D/output/14'
for downloaduri in globaldownloadurilist:
    r = requests.get(downloaduri, auth=(CRA_USER, PASSWORD), headers=headers)
    sys.stderr.write("%s\n" % r.headers)
    import re
    d = r.headers['content-disposition']
    fname_list = re.findall("filename=(.+)", d)
    for fname in fname_list:
        sys.stderr.write("%s\n" % fname)

# download all output files

import re
#downloaduri = 'https://cipresrest.sdsc.edu/cipresrest/v1/job/kenneth/NGBW-JOB-RAXMLHPC8_REST_XSEDE-EF0E26B61D2E4C0C8D02499D8068D873/output/11496'
for downloaduri in globaldownloadurilist:
    r = requests.get(downloaduri, auth=(CRA_USER, PASSWORD), headers=headers)
    #sys.stderr.write("%s\n" % r.json())
    #r.content
    d = r.headers['content-disposition']
    filename_list = re.findall('filename=(.+)', d)
    for filename in filename_list:
        #http://docs.python-requests.org/en/master/user/quickstart/#raw-response-content
        with open(filename, 'wb') as fd:
            for chunk in r.iter_content():
                fd.write(chunk)

# get a list of jobs for user and app key, and terminalStage status

r = requests.get("%s/job/%s" % (URL,CRA_USER), auth=(CRA_USER, PASSWORD), headers=headers)
#print(r.text)

root = xml.etree.ElementTree.fromstring(r.text)
for child in root:
    if child.tag == 'jobs':
        for jobchild in child:
            if jobchild.tag == 'jobstatus':
                for statuschild in jobchild:
                    if statuschild.tag == 'selfUri':
                        for selfchild in statuschild:
                            if selfchild.tag == 'url':
                                #print(child)
                                joburi = selfchild.text
                                jobr = requests.get(joburi, auth=(CRA_USER, PASSWORD), headers=headers)
                                jobroot = xml.etree.ElementTree.fromstring(jobr.text)
                                for jobrchild in jobroot:
                                    if jobrchild.tag == 'terminalStage':
                                        jobstatus = jobrchild.text
                                        sys.stdout.write("job url: %s status terminalStage: %s\n" % (joburi,jobstatus))


# get information for a single job, print out raw XML, need to set joburi according to above list

joburi = 'https://nsgr.sdsc.edu:8443/cipresrest/v1/job/kenneth/NGBW-JOB-NEURON73_TG-220F7B3C7EE84BC3ADD87346E933ED5E'
r = requests.get(joburi,
                 headers= headers, auth=(CRA_USER, PASSWORD))
print(r.text)

# delete an old job, need to set joburi
joburi = 'https://nsgr.sdsc.edu:8443/cipresrest/v1/job/kenneth/NGBW-JOB-NEURON73_TG-7AF604008F314B43A331231E5A94C361'
r = requests.delete(joburi, auth=(CRA_USER, PASSWORD), headers=headers)
sys.stderr.write("%s\n" % r.text)

