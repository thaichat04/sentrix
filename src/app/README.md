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


## Online demos

```shell script
>>> curl -X POST -F 'input=give your input (happy or not happy) here' http://host:5000/v0/classify
[
    {
        "label": "NEGATIVE",
        "score": 0.9605754017829895
    }
]
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
 1 node: online prediction (hardware, prediction optimisation)
 N nodes: load balancing
 batch processing (API)

## Availability
- safety shutdown
- healthcheck
