#!/bin/sh

. `dirname $0`/../settings.sh

$ES_BASE_PATH/bin/plugin -install mobz/elasticsearch-head
$ES_BASE_PATH/bin/plugin -install royrusso/elasticsearch-HQ
#$ES_BASE_PATH/bin/plugin -install elasticsearch/marvel/latest
$ES_BASE_PATH/bin/plugin -install polyfractal/elasticsearch-inquisitor
$ES_BASE_PATH/bin/plugin -install elasticsearch/elasticsearch-analysis-kuromoji/2.0.0
$ES_BASE_PATH/bin/plugin -install elasticsearch/elasticsearch-mapper-attachments/2.0.0
$ES_BASE_PATH/bin/plugin -install com.github.richardwilly98.elasticsearch/elasticsearch-river-mongodb/2.0.0
