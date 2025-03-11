# service-scheduler

A SAM application which starts/stops ECS services and autoscaling groups based on their tags.

## 📌 Table of Contents

  - [👨‍🔬 Test](#local-invoke)
  - [👷 Deploy](#deploy)
    - [Local](#local)
    - [Pipeline](#pipeline)
  - [⚙️ Configuration](#configuration)
  - [🔨 Service Scheduling Configuration](#fix-rds)
  - [📜 License](#license)

## Overview
A SAM application which starts/stops ECS services and autoscaling groups based on their tags. This solution extend [instance-scheduler-on-aws](https://github.com/aws-solutions/instance-scheduler-on-aws).
Adding support for schedule:
- ECS Task
- EC2 Autoscaling
- Fix RDS Cluster shutdown, for instance and Cluster that cannot shutdown by instance scheduler after restart by one week from shutdown.

## 👨‍🔬 Test <a name="test"></a>

### Local invocation <a name="local-invoke"></a>

`sam build && sam local invoke --env-vars local-env.json --event events/cwevent.json --profile <profile-name>`

The function is run on a periodic cloudwatch event.
The configurations of the scheduled services are compared to the event's time
To test for different event timestamps, change the property `"time"` in `events/cwevent.json`


## 👷 Deploy <a name="deploy"></a>

### Local

`sam build --config-env dev && sam deploy --config-env dev`

### Pipeline

You can deploy this application using AWS Pipeline.

For deploy using pipeline you need:
1. Deploy pipiline using module `epsilonline/sam-app-pipeline/aws`. You can find example in folder **tests\terraform**.
2. Prepare zip for pipeline
    ```Bash
    zip -r source.zip . -x ./venv/\* ./.git/\* ./terraform-modules/\* ./.aws_sam/\* ./.idea/\* ./.aws-sam/\* ./tests/\* .gitignore
    ```
3. Copy source.zip in **Source bucket**
4. Eventually approve pipeline
5. Check status in cloudformation console
6. Enjoy!

## ⚙️ Configuration <a name="configuration"></a>

For configure backup tags and scheduler period refer to configuration of [instance-scheduler-on-aws](https://docs.aws.amazon.com/solutions/latest/instance-scheduler-on-aws/operator-guide.html#configure-schedules)

### Log level
You can change the lambda function logging level by changing the TRACE lambda environment variable to:

- "yes" -> Enable DEBUG level
- "no" -> Enable INFO level

## 🔨 Fix RDS Scheduling Configuration <a name="fix-rds"></a>

The cloudformation stack can schedule EC2 instances and RDS instances with the *ScheduledServices* parameter, that can be set to values "EC2", "RDS" or "Both".
Note that in case of RDS clusters, you have to enable two more flags:

- *ScheduleRdsClusters*         = "Yes"
- *EnableSSMMaintenanceWindows* = "Yes"

## 📜 License <a name="license"></a>

This project is licensed under the [**LGPL-3 License**](https://www.gnu.org/licenses/lgpl-3.0.html#license-text).
