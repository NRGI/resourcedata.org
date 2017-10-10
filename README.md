# resourcedata.org
CKAN

## SOLR setup

- Follow steps 1-3 from this quickstart guide: https://www.measuredsearch.com/docs/ 
- After you unzip the archive downloaded from point 3 in the guide, you will need to overwrite the schema with the ckan one. The ckan solr schema can be found at `ckan/config/solr/schema.xml` in the project. Copy the `schema.xml` file over the `searchstax-client-master/solr-5/configsets/basic_configs/conf/schema.xml` file, where `searchstax-client-master` is the root of the folder unzipped at point 3 from the guide.
Something like this: 
```
cp ~/nrgi-resourcedata.org/ckan/config/solr/schema.xml searchstax-client-master/solr-5/configsets/basic_configs/conf/schema.xml
```
- Now continue executing the instructions from the guide. 
- At point 4 in the guide this is the command we used (you have to be in the scripts folder, as mentioned in the guide):
```
./zkcli.sh -zkhost ss288577-1-zk-us-east-1-aws.measuredsearch.com:2181 -cmd upconfig -confdir ../configsets/basic_configs/conf/ -confname ckan
```
- At point 5 we run two commands to create the collections, one for master, one for staging
- master:
```
curl 'https://ss288577-us-east-1-aws.measuredsearch.com/solr/admin/collections?action=CREATE&name=master&collection.configName=ckan&numShards=1'
```
- staging:
```
curl 'https://ss288577-us-east-1-aws.measuredsearch.com/solr/admin/collections?action=CREATE&name=staging&collection.configName=ckan&numShards=1'
```
And this should finalize the config. To test the indexes you can use these links:
staging:
```
curl https://ss288577-us-east-1-aws.measuredsearch.com/solr/staging/query
```
master:
```
curl https://ss288577-us-east-1-aws.measuredsearch.com/solr/master/query
```

Note that we have no authentication, if someone knows the link they have full admin access.

The steps documented above are already executed. From here on, the ECS services (and optionally the docker-compose file) will have to be modified.

We will have to set the links in the CKAN container definitions. We will use the SOLR_URL variable which will contain one of the two master/staging links below. Use the master link for master, staging link for staging:
master: `https://ss288577-us-east-1-aws.measuredsearch.com/solr/master`
staging:`https://ss288577-us-east-1-aws.measuredsearch.com/solr/staging`

The old SOLR_PORT_8983_TCP_ADDR and PORT variables will be no longer used. Also the solr container will no longer be used.

After the link to the hosted solr is up, we should rebuild the index, as specified by Matt above.

## Reindex datasets
Connect to the CKAN container and run the following:
```
cd /usr/lib/ckan/default
./bin/paster --plugin=ckan search-index check --config=/etc/ckan/default/ckan.ini
```
