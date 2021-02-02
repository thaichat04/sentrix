<!---
Copyright 2020 The HuggingFace Team. All rights reserved.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
-->

<p align="center">
    <br>
    <img src="https://raw.githubusercontent.com/huggingface/transformers/master/docs/source/imgs/transformers_logo_name.png" width="400"/>
    <br>
<p>

<h3 align="center">
<p>Sentrix, On-line API service for sentiment analysis powered by pipeline Transformers</p>
</h3>


### DoD

- [x] Pipeline Transformer integration
- [x] Business Use case
- [x] (Simple) API implementation
- [x] Deploy on Cloud (GKE)
- [x] Benchmark & loading test
- [ ] Monitoring by Grafana/Prometheus

## Online demos
- KGE deployement: http://35.202.245.141/version


## curl
```shell script
>>> curl -X POST -F 'input=give your input (happy or not happy) here' http://host:5000/v0/classify
[
    {
        "label": "NEGATIVE",
        "score": 0.9605754017829895
    }
]

curl -X POST -F 'input=give your input (happy or not happy) here' http://35.202.245.141/v0/classify
```

## Build & Run
```shell script
>>> docker build --tag sentrix:tag_version

>>> docker pull thaichat04/sentrix
>>> docker run -it -p 5000:5000 -e PYTORCH_TRANSFORMERS_CACHE=/cache/pyt -v /tmp/pyt:/cache/pyt thaichat04/sentrix:tag_version
```

## Benchmark
```shell script
>>> pip3 install locust
>>> cd src/test
>>> locust -f benchmark.py -h http://35.202.245.141
```
Fixed Input text: 166 chars
#### 1 user, 1 spawn rate
```
Name                                                          # reqs      # fails  |     Avg     Min     Max  Median  |   req/s failures/s
--------------------------------------------------------------------------------------------------------------------------------------------
 POST /v0/classify                                                 33     0(0.00%)  |     347     313     512     330  |    0.62    0.00
--------------------------------------------------------------------------------------------------------------------------------------------
 Aggregated                                                        33     0(0.00%)  |     347     313     512     330  |    0.62    0.00

Response time percentiles (approximated)
 Type     Name                                                              50%    66%    75%    80%    90%    95%    98%    99%  99.9% 99.99%   100% # reqs
--------|------------------------------------------------------------|---------|------|------|------|------|------|------|------|------|------|------|------|
 POST     /v0/classify                                                      330    330    340    380    420    460    510    510    510    510    510     33
--------|------------------------------------------------------------|---------|------|------|------|------|------|------|------|------|------|------|------|
 None     Aggregated                                                        330    330    340    380    420    460    510    510    510    510    510     33
 ```
#### 10 users, 5 spawn rate
```
 Name                                                          # reqs      # fails  |     Avg     Min     Max  Median  |   req/s failures/s
--------------------------------------------------------------------------------------------------------------------------------------------
 POST /v0/classify                                                269     5(1.86%)  |     380     221    1819     350  |    5.28    0.10
--------------------------------------------------------------------------------------------------------------------------------------------
 Aggregated                                                       269     5(1.86%)  |     380     221    1819     350  |    5.28    0.10

Response time percentiles (approximated)
 Type     Name                                                              50%    66%    75%    80%    90%    95%    98%    99%  99.9% 99.99%   100% # reqs
--------|------------------------------------------------------------|---------|------|------|------|------|------|------|------|------|------|------|------|
 POST     /v0/classify                                                      350    370    380    390    420    480    980   1400   1800   1800   1800    269
--------|------------------------------------------------------------|---------|------|------|------|------|------|------|------|------|------|------|------|
 None     Aggregated                                                        350    370    380    390    420    480    980   1400   1800   1800   1800    269

Error report
 # occurrences      Error
--------------------------------------------------------------------------------------------------------------------------------------------
 5                  POST /v0/classify: HTTPError('500 Server Error: INTERNAL SERVER ERROR for url: http://35.202.245.141/v0/classify')
--------------------------------------------------------------------------------------------------------------------------------------------
```
#### 50 users, 30 spawn rate
```
 Name                                                          # reqs      # fails  |     Avg     Min     Max  Median  |   req/s failures/s
--------------------------------------------------------------------------------------------------------------------------------------------
 POST /v0/classify                                               1567    34(2.17%)  |    1532     220   78724    1300  |   16.62    0.36
--------------------------------------------------------------------------------------------------------------------------------------------
 Aggregated                                                      1567    34(2.17%)  |    1532     220   78724    1300  |   16.62    0.36

Response time percentiles (approximated)
 Type     Name                                                              50%    66%    75%    80%    90%    95%    98%    99%  99.9% 99.99%   100% # reqs
--------|------------------------------------------------------------|---------|------|------|------|------|------|------|------|------|------|------|------|
 POST     /v0/classify                                                     1300   1900   2200   2300   2900   3200   3400   3700  72000  79000  79000   1567
--------|------------------------------------------------------------|---------|------|------|------|------|------|------|------|------|------|------|------|
 None     Aggregated                                                       1300   1900   2200   2300   2900   3200   3400   3700  72000  79000  79000   1567

Error report
 # occurrences      Error
--------------------------------------------------------------------------------------------------------------------------------------------
 33                 POST /v0/classify: HTTPError('500 Server Error: INTERNAL SERVER ERROR for url: http://35.202.245.141/v0/classify')
 1                  POST /v0/classify: ConnectionError(MaxRetryError("HTTPConnectionPool(host='35.202.245.141', port=80): Max retries exceeded with url: /v0/classify (Caused by NewConnectionError('<urllib3.connection.HTTPConnection object at 0x7fb51070b9a0>: Failed to establish a new connection: [Errno 60] Operation timed out'))"))
```

#### 1000 users, 500 spawn rate
```
 Name                                                          # reqs      # fails  |     Avg     Min     Max  Median  |   req/s failures/s
--------------------------------------------------------------------------------------------------------------------------------------------
 POST /v0/classify                                               1515  399(26.34%)  |   20544     242   53779   19000  |   27.39    7.21
--------------------------------------------------------------------------------------------------------------------------------------------
 Aggregated                                                      1515  399(26.34%)  |   20544     242   53779   19000  |   27.39    7.21

Response time percentiles (approximated)
 Type     Name                                                              50%    66%    75%    80%    90%    95%    98%    99%  99.9% 99.99%   100% # reqs
--------|------------------------------------------------------------|---------|------|------|------|------|------|------|------|------|------|------|------|
 POST     /v0/classify                                                    19000  23000  28000  30000  34000  38000  44000  49000  53000  54000  54000   1515
--------|------------------------------------------------------------|---------|------|------|------|------|------|------|------|------|------|------|------|
 None     Aggregated                                                      19000  23000  28000  30000  34000  38000  44000  49000  53000  54000  54000   1515

Error report
 # occurrences      Error
--------------------------------------------------------------------------------------------------------------------------------------------
 124                POST /v0/classify: HTTPError('500 Server Error: INTERNAL SERVER ERROR for url: http://35.202.245.141/v0/classify')
 275                POST /v0/classify: ConnectionError(ProtocolError('Connection aborted.', ConnectionResetError(54, 'Connection reset by peer')))
--------------------------------------------------------------------------------------------------------------------------------------------
```

## Business case

Sentiments analysis are important in many fields: recommendation, customer services ...
Input are generally comments, feedback from user about some products, services. Find out nagative/positive from clients are crucial.
In some case, analysis of feedback must be in real time to be react ASAP from customer service. With a huge incoming data content, AI is the best option.

### Requirements

* Input (limited max 250 words) in plain text (no HTML or other formats)
* Output: Nagative/Positive + Score
* Response time < 50ms

### TODO
* Automatic build/version/release setup
* IT
* Coverage & Sonar metrix

### Openings
* Language detection, language specialized
* Domain specialized classification
* Batch processing
* build models API
* load models API
* tuning model API
* Authentication
* Quota control & pricing
* Exploitation: BI & dashboard by account

## Scalability
* 1 node: online prediction (hardware, prediction optimisation)
* N nodes: load balancing
* batch processing (API)

## Availability
* safety shutdown
* healthcheck
* crash recovery
