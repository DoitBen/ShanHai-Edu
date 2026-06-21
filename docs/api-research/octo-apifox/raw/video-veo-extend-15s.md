# Veo （延长至15s）

## OpenAPI Specification

```yaml
openapi: 3.0.1
info:
  title: ''
  description: ''
  version: 1.0.0
paths:
  /v1/videos:
    post:
      summary: Veo （延长至15s）
      deprecated: false
      description: >-
        # Veo 视频延长（Remix）接口文档


        ## 接口地址

        `POST /v1/videos`


        ## 功能说明

        支持对已有视频进行延长处理（Remix），基于原视频内容生成续集视频。


        **模型**：`veo_3_1-fast-extend`  


        ## 时效性说明


        **视频延长有效期**：视频生成后的 12 小时内可以进行延长处理，超过 12 小时可能失败。


        **说明**：建议在视频生成后尽快进行延长操作，以确保延长功能正常工作。


        ## 请求方式


        **本接口支持两种提交方式：**

        - `multipart/form-data`（推荐）

        - `application/json`


        ## 请求头


        | 参数名 | 类型 | 必填 | 说明 |

        |--------|------|------|------|

        | Authorization | string | 是 | `Bearer YOUR_API_KEY` |

        | Content-Type | string | 否 | `multipart/form-data` 或 `application/json`
        |


        ## 请求参数



        ### multipart/form-data 方式


        | 参数名 | 类型 | 必填 | 说明 |

        |--------|------|------|------|

        | model | string | 是 | 固定值：`veo_3_1-fast-extend` |

        | remix_id | string | 是 | 原视频的 video_id（格式：`video_xxx`） |

        | prompt | string | 是 | 延长视频的提示词描述 |


        ### remix_id 参数获取方法


        `remix_id` 是原视频的 video_id，格式为 `video_xxxx`。有以下两种获取方法：


        **方法 1：从任务提交返回的 JSON 中获取（推荐）**

        - 在任务提交成功后，立即从返回的 JSON 中获取 `data.remix_id` 字段

        - 例如：`"remix_id": "video_56c98f84-001b-41ea-9542-5290279f4827"`


        **方法 2：从任务提交返回的 JSON 中获取 `data.size`**

        - 如果返回的 JSON 中没有显示 `data.remix_id`，可以使用 `data.size` 字段

        - 在任务提交成功时，`data.size` 字段的值与 `remix_id` 相同（格式：`video_xxxx`）

        - 例如：`"size": "video_56c98f84-001b-41ea-9542-5290279f4827"`

        - 注意：当任务状态变为处理中或完成时，`data.size` 可能会自动恢复为视频尺寸（如 `"720x720"`）


        **注意**：建议在任务提交成功后立即获取并保存 `remix_id`，避免后续状态变化导致字段值改变。


        ### application/json 方式


        ```json

        {
          "model": "veo_3_1-fast-extend",
          "remix_id": "video_xxx",
          "prompt": "延长视频的提示词"
        }

        ```


        ## 请求示例


        ### multipart/form-data 示例


        ```bash

        curl -X POST "https://your-gateway.com/v1/videos" \
          -H "Authorization: Bearer YOUR_API_KEY" \
          -F "model=veo_3_1-fast-extend" \
          -F "remix_id=video_56c98f84-001b-41ea-9542-5290279f4827" \
          -F "prompt=鼠标再次点一下，电脑关机了" 
        ```


        ### JSON 示例


        ```bash

        curl -X POST "https://your-gateway.com/v1/videos" \
          -H "Authorization: Bearer YOUR_API_KEY" \
          -H "Content-Type: application/json" \
          -d '{
            "model": "veo_3_1-fast-extend",
            "remix_id": "video_56c98f84-001b-41ea-9542-5290279f4827",
            "prompt": "鼠标再次点一下，电脑关机了"
          }'
        ```


        ## 响应参数


        | 参数名 | 类型 | 说明 |

        |--------|------|------|

        | id | string | 任务ID |

        | task_id | string | 任务ID（与id相同） |

        | object | string | 对象类型，固定值：video |

        | model | string | 使用的模型名称 |

        | status | string |
        任务状态：queued（排队中）、processing（处理中）、completed（已完成）、failed（失败） |

        | progress | number | 任务进度，0-100 |

        | created_at | number | 创建时间戳（秒） |

        | size | string | 视频尺寸 |

        | remixed_from_video_id | string | 原视频ID |


        ## 响应示例


        ### 提交成功（排队中）


        ```json

        {
          "id": "task_pMjFpn4z0keL4KoxrxRnwNAAmRcWSKp4",
          "task_id": "task_pMjFpn4z0keL4KoxrxRnwNAAmRcWSKp4",
          "object": "video",
          "model": "veo_3_1-fast-extend",
          "status": "queued",
          "progress": 0,
          "created_at": 1775647662,
          "size": "720x720",
          "remixed_from_video_id": "56c98f84-001b-41ea-9542-5290279f4827"
        }

        ```


        ## 查询任务状态


        ### 接口地址

        `GET /v1/videos/{task_id}`


        ### 请求示例


        ```bash

        curl -X GET
        "https://your-gateway.com/v1/videos/task_pMjFpn4z0keL4KoxrxRnwNAAmRcWSKp4"
        \
          -H "Authorization: Bearer YOUR_API_KEY"
        ```


        ### 任务完成响应示例


        ```json

        {
          "id": 857120,
          "created_at": 1775648631,
          "updated_at": 1775648745,
          "task_id": "task_ijG7C2LGkRMnZK9EvB0orFGe3Few6yFz",
          "platform": "1",
          "user_id": 4,
          "group": "default",
          "channel_id": 6,
          "quota": 30000,
          "action": "textGenerate",
          "status": "SUCCESS",
          "fail_reason": "",
          "result_url": "https://xxxxx.com/v1/videos/task_ijG7C2LGkRMnZK9EvB0orFGe3Few6yFz/content",
          "submit_time": 1775648631,
          "start_time": 0,
          "finish_time": 1775648745,
          "progress": "100%",
          "properties": {
            "input": "",
            "upstream_model_name": "veo_3_1-fast",
            "origin_model_name": "veo_3_1-fast"
          },
          "username": "otuapi",
          "data": {
            "id": "task_ijG7C2LGkRMnZK9EvB0orFGe3Few6yFz",
            "size": "720x1280",
            "model": "veo_3_1-fast",
            "object": "video",
            "status": "completed",
            "seconds": "1",
            "remix_id": "video_002546c9-ec66-405b-89ab-4d50cc59bb45",
            "video_url": "https://videos-us3.ss2.life/ai-sandbox-videofx/video/...",
            "created_at": 1775648631,
            "completed_at": 1775648733
          },
          "timestamp2string": "2026-04-08 19:43:51",
          "key": "857120"
        }

        ```


        ## 注意事项



        1. **延长时长**：目前仅支持延长至 15 秒。


        2. **时效性**：视频生成后的 12 小时内可以进行延长处理，超过 12 小时可能失败。


        3. **异步模式**：提交成功仅返回任务 id，须轮询 `GET /v1/videos/{task_id}` 获取进度与结果。


        4. **视频获取**：任务完成后，通过 `data.video_url` 获取视频地址。
      tags:
        - 视频生成（Videos）
      parameters:
        - name: Authorization
          in: header
          description: ''
          required: true
          example: Bearer {{YOUR_API_KEY}}
          schema:
            type: string
        - name: Content-Type
          in: header
          description: ''
          required: false
          example: multipart/form-data
          schema:
            type: string
      requestBody:
        content:
          multipart/form-data:
            schema:
              type: object
              properties:
                model:
                  example: veo_3_1-fast-extend
                  type: string
                prompt:
                  example: 一只猫在追一条狗
                  type: string
                remix_id:
                  description: 这个值是返回的`data.remix_id`，注意不是task_id
                  example: video_002546c9-ec66-405b-89ab-4d50cc59bb45
                  type: string
              required:
                - model
                - prompt
                - remix_id
            examples: {}
      responses:
        '200':
          description: ''
          content:
            application/json:
              schema:
                type: object
                properties:
                  id:
                    type: integer
                  created_at:
                    type: integer
                  updated_at:
                    type: integer
                  task_id:
                    type: string
                  platform:
                    type: string
                  user_id:
                    type: integer
                  group:
                    type: string
                  channel_id:
                    type: integer
                  quota:
                    type: integer
                  action:
                    type: string
                  status:
                    type: string
                  fail_reason:
                    type: string
                  result_url:
                    type: string
                  submit_time:
                    type: integer
                  start_time:
                    type: integer
                  finish_time:
                    type: integer
                  progress:
                    type: string
                  properties:
                    type: object
                    properties:
                      input:
                        type: string
                      upstream_model_name:
                        type: string
                      origin_model_name:
                        type: string
                    required:
                      - input
                      - upstream_model_name
                      - origin_model_name
                    x-apifox-orders:
                      - input
                      - upstream_model_name
                      - origin_model_name
                  username:
                    type: string
                  data:
                    type: object
                    properties:
                      id:
                        type: string
                      size:
                        type: string
                      model:
                        type: string
                      object:
                        type: string
                      status:
                        type: string
                      remix_id:
                        type: string
                      expire_at:
                        type: integer
                      video_url:
                        type: string
                      created_at:
                        type: integer
                      completed_at:
                        type: integer
                      storage_type:
                        type: string
                      remixed_from_video_id:
                        type: string
                    required:
                      - id
                      - size
                      - model
                      - object
                      - status
                      - remix_id
                      - expire_at
                      - video_url
                      - created_at
                      - completed_at
                      - storage_type
                      - remixed_from_video_id
                    x-apifox-orders:
                      - id
                      - size
                      - model
                      - object
                      - status
                      - remix_id
                      - expire_at
                      - video_url
                      - created_at
                      - completed_at
                      - storage_type
                      - remixed_from_video_id
                  timestamp2string:
                    type: string
                  key:
                    type: string
                required:
                  - id
                  - created_at
                  - updated_at
                  - task_id
                  - platform
                  - user_id
                  - group
                  - channel_id
                  - quota
                  - action
                  - status
                  - fail_reason
                  - result_url
                  - submit_time
                  - start_time
                  - finish_time
                  - progress
                  - properties
                  - username
                  - data
                  - timestamp2string
                  - key
                x-apifox-orders:
                  - id
                  - created_at
                  - updated_at
                  - task_id
                  - platform
                  - user_id
                  - group
                  - channel_id
                  - quota
                  - action
                  - status
                  - fail_reason
                  - result_url
                  - submit_time
                  - start_time
                  - finish_time
                  - progress
                  - properties
                  - username
                  - data
                  - timestamp2string
                  - key
              example:
                id: 35
                created_at: 1775646650
                updated_at: 1775646780
                task_id: task_qP9bL7PzkpgL8PdofH7z5sgTSOAX1Cmr
                platform: '1'
                user_id: 1
                group: svip
                channel_id: 3
                quota: 1200000
                action: textGenerate
                status: SUCCESS
                fail_reason: ''
                result_url: >-
                  https://api.xxxxxx.com/v1/videos/task_qP9bL7PzkpgL8PdofH7z5sgTSOAX1Cmr/content
                submit_time: 1775646650
                start_time: 1775646732
                finish_time: 1775646780
                progress: 100%
                properties:
                  input: ''
                  upstream_model_name: veo_3_1-fast-extend
                  origin_model_name: veo_3_1-fast-extend
                username: xxxx
                data:
                  id: task_Pdnr4vROpcAJoum2wRJgnFDQxM6SNCWz
                  size: 720x720
                  model: veo_3_1-fast-extend
                  object: video
                  status: completed
                  remix_id: video_6d214236-a53d-4d05-add6-d7bda815dd46
                  expire_at: 1775664774408
                  video_url: >-
                    https://veo.xxxxx.com/videos/video_6d214236-a53d-4d05-add6-d7bda815dd46_1775646774391_0070b318.mp4
                  created_at: 1775646650
                  completed_at: 1775646764
                  storage_type: local
                  remixed_from_video_id: 56c98f84-001b-41ea-9542-5290279f4827
                timestamp2string: '2026-04-08 19:10:50'
                key: '35'
          headers: {}
          x-apifox-name: 成功
      security: []
      x-apifox-folder: 视频生成（Videos）
      x-apifox-status: developing
      x-run-in-apifox: https://app.apifox.com/web/project/7902379/apis/api-440214130-run
components:
  schemas: {}
  securitySchemes: {}
servers: []
security: []

```
