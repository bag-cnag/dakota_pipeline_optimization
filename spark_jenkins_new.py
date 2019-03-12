#!/usr/bin/env python

# Read DAKOTA parameters file (aprepro or standard format) and call a
# Python module rosenbrock for analysis.  Uses same rosenbrock.py as
# linked case for consistency.

# DAKOTA will execute this script as
#   rosenbrock_bb.py params.in results.out
# so sys.argv[1] will be the parameters file and
#    sys.argv[2] will be the results file to return to DAKOTA

# necessary python modules
import sys
import re
import os
import requests,urllib,json,time

# ----------------------------
# Parse DAKOTA parameters file
# ----------------------------

# setup regular expressions for parameter/label matching
e = '-?(?:\\d+\\.?\\d*|\\.\\d+)[eEdD](?:\\+|-)?\\d+' # exponential notation
f = '-?\\d+\\.\\d*|-?\\.\\d+'                        # floating point
i = '-?\\d+'                                         # integer
value = e+'|'+f+'|'+i                                # numeric field
tag = '\\w+(?::\\w+)*'                               # text tag field

# regular expression for aprepro parameters format
aprepro_regex = re.compile('^\s*\{\s*(' + tag + ')\s*=\s*(' + value +')\s*\}$')
# regular expression for standard parameters format
standard_regex = re.compile('^\s*(' + value +')\s+(' + tag + ')$')

# open DAKOTA parameters file for reading
paramsfile = open(sys.argv[1], 'r')

# extract the parameters from the file and store in a dictionary
paramsdict = {}
for line in paramsfile:
    m = aprepro_regex.match(line)
    if m:
        paramsdict[m.group(1)] = m.group(2)
    else:
        m = standard_regex.match(line)
        if m:
            paramsdict[m.group(2)] = m.group(1)

paramsfile.close()

# crude error checking; handle both standard and aprepro cases
num_vars = 0
if ('variables' in paramsdict):
    num_vars = int(paramsdict['variables'])
elif ('DAKOTA_VARS' in paramsdict):
    num_vars = int(paramsdict['DAKOTA_VARS'])

num_fns = 0
if ('functions' in paramsdict):
    num_fns = int(paramsdict['functions'])
elif ('DAKOTA_FNS' in paramsdict):
    num_fns = int(paramsdict['DAKOTA_FNS'])

if (num_vars != 2 or num_fns != 1):
    print("Rosenbrock requires 2 variables and 1 function;\nfound " + \
   str( num_vars) + " variables and " + str(num_fns) + " functions.") 
    sys.exit(1)


# -------------------------------
# Convert and send to application
# -------------------------------

# set up the data structures the rosenbrock analysis code expects
# for this simple example, put all the variables into a single hardwired array
continuous_vars = [ float(paramsdict['cpu']), float(paramsdict['memory']) ]
active_set_vector = [ int(paramsdict['ASV_1:obj_fn']) ] 

# set a dictionary for passing to rosenbrock via Python kwargs
rosen_params = {}
rosen_params['cv'] = continuous_vars
rosen_params['asv'] = active_set_vector
rosen_params['functions'] = 1

username=os.environ['username']
jenkins_token=os.environ['jenkins_token']
jenkins_token_name="ddptoken"
prefix_url="172.16.10.5/service/jenkins"
mesos_master="10.3.0.102"
chrom="10"
# execute the rosenbrock analysis as a separate Python module
print("Running rosenbrock...")
headers = {'Content-Type': 'application/x-www-form-urlencoded'}  
from rosenbrock import rosenbrock_list
#import ipdb;ipdb.set_trace()
url_job="vcfLoaderStep-uspark"
respost = requests.get("http://username:jenkins_token@"+prefix_url+"/job/"+url_job+"/lastSuccessfulBuild/api/json?token="+jenkins_token_name)
#params= {"json":{'parameter': { 'name': 'prova', 'value': paramsdict['cpu']}}}

params= {"json":{'parameter': [{"name":"chrom", "value":chrom},{"name":"master", "value":mesos_master},{"name":"cores", "value":paramsdict["cpu"]},{"name":"executor_memory", "value":paramsdict['memory']+"G"},{"name":"step", "value":"annotateVEP"},{"name":"nchroms", "value":"1"},{"name":"config_path", "value":"/tmp/dakota/config.json"}]}}

r = requests.post("http://username:jenkins_token@"+prefix_url+"/job/"+url_job+"/build?token="+jenkins_token_name, data=urllib.parse.urlencode(params), headers=headers)

previous_job= json.loads(respost.text)["number"] 
rosen_results = rosenbrock_list(**rosen_params)
print("previos job is "+str(previous_job))
cycle=True
while cycle:

    respost = requests.get("http://username:jenkins_token@"+prefix_url+"/job/"+url_job+"/lastSuccessfulBuild/api/json?token="+jenkins_token_name)
    
    if (json.loads(respost.text)['number']==previous_job+1):
        print("job ended")
        cycle=False
        duration= json.loads(respost.text)["duration"] 
        print("it took "+str(duration))
    else:
        print ("running job is"+str(json.loads(respost.text)['number']+1))
        time.sleep(5)


print ("Rosenbrock complete.")


# ----------------------------
# Return the results to DAKOTA
# ----------------------------

# write the results.out file for return to DAKOTA
# this example only has a single function, so make some assumptions;
# not processing DVV
outfile = open('results.out.tmp', 'w')

# write functions
   
outfile.write(str(duration) + '\n')


outfile.close()

# move the temporary results file to the one DAKOTA expects
import shutil
shutil.move('results.out.tmp', sys.argv[2])
#os.system('mv results.out.tmp ' + sys.argv[2])
