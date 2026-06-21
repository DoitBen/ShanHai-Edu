# veo（直出15s）

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
      summary: veo（直出15s）
      deprecated: false
      description: >
        # Veo 15秒视频生成接口文档


        ## 接口地址

        `POST /v1/videos`


        ## 功能说明


        支持 Veo 模型生成 **15 秒**视频（8s + 7s 自动延长），涵盖文生视频和图生视频：


        - **文生视频 15s**：使用 `veo_3_1-fast-remix` 模型

        - **图生视频首尾帧 15s**：使用 `veo_3_1-fast-fl-remix` 模型，支持 1～2 张图片作为首尾帧

        - **图生视频参考图 15s**：使用 `veo_3_1-fast-remix` 模型，支持最多 3 张参考图片

        - **高清文生视频 15s**：使用 `veo_3_1-fast-hd-remix` 模型

        - **高清首尾帧 15s**：使用 `veo_3_1-fast-fl-hd-remix` 模型


        > 模型命名规则：在原有 8 秒模型名称后加 `-remix` 后缀即为 15 秒版本。


        ## 请求方式


        **本接口仅支持 `multipart/form-data`。**


        文生视频同样使用 form-data，仅不传图片字段即可。


        ## 请求头


        | 参数名 | 类型 | 必填 | 说明 |

        |--------|------|------|------|

        | Authorization | string | 是 | `Bearer YOUR_API_KEY` |

        | Content-Type | string | — | `multipart/form-data` |


        ## 表单字段说明


        | 参数名 | 类型 | 必填 | 说明 |

        |--------|------|------|------|

        | model | string | 是 | 模型名称（见下方模型列表） |

        | prompt | string | 是 | 第一段视频（前 8 秒）的提示词 |

        | prompt_extend | string | 是 | 延长部分（后 7 秒）的提示词 |

        | size | string | 否 | 视频尺寸，格式 `widthxheight`，如 `1280x720`、`1920x1080` |

        | input_reference[] | 可重复 | 否 | 图生视频时传递，同一字段名可重复多次。文生视频不携带本字段。 |


        ## 模型列表


        | 模型名称 | 说明 |

        |----------|------|

        | `veo_3_1-fast-remix` | Fast 文生视频 / 参考图 15s |

        | `veo_3_1-fast-fl-remix` | Fast 首尾帧 15s |

        | `veo_3_1-fast-hd-remix` | Fast 高清文生视频 / 参考图 15s（1080p） |

        | `veo_3_1-fast-fl-hd-remix` | Fast 高清首尾帧 15s（1080p） |

        | `veo_3_1-hd-remix` | 高质量文生视频 / 参考图 15s（1080p） |

        | `veo_3_1-hd-fl-remix` | 高质量首尾帧 15s（1080p） |

        | `veo_3_1-remix` | 标准文生视频 / 参考图 15s |

        | `veo_3_1-fl-remix` | 标准首尾帧 15s |


        ## `input_reference[]` 的三种传法


        | 方式 | 说明 |

        |------|------|

        | **本地文件** | multipart 里以文件部件提交，例如 curl 的 `-F
        "input_reference[]=@/path/to/image.jpg"` |

        | **图片 URL** | 以普通表单文本提交**可公网访问的图片直链**，例如 `-F
        "input_reference[]=https://example.com/a.png"` |

        | **Base64** | 以文本字段提交完整 data URI，例如 `-F
        "input_reference[]=data:image/jpeg;base64,/9j/4AAQ..."` |


        **顺序约定**：

        - **首尾帧模式**：第 1 个 `input_reference[]` 为首帧，第 2 个为尾帧；仅 1 个时表示只指定首帧。

        - **参考图模式**：最多 3 个 `input_reference[]`，顺序为参考图 1、2、3。


        ---


        ## 请求示例


        ### 文生视频 15s

        ```bash

        curl -X POST "https://api.example.com/v1/videos" \
          -H "Authorization: Bearer YOUR_API_KEY" \
          -F "model=veo_3_1-fast-remix" \
          -F "prompt=一只可爱的小猫在花园里奔跑" \
          -F "prompt_extend=小猫跳过花丛，追逐一只蝴蝶" \
          -F "size=1920x1080"
        ```


        ### 高清首尾帧 15s · 本地文件

        ```bash

        curl -X POST "https://api.example.com/v1/videos" \
          -H "Authorization: Bearer YOUR_API_KEY" \
          -F "model=veo_3_1-fast-fl-hd-remix" \
          -F "prompt=让这两张图之间自然过渡" \
          -F "prompt_extend=画面继续展开，镜头缓缓拉远" \
          -F "size=1920x1080" \
          -F "input_reference[]=@/path/to/first_frame.jpg" \
          -F "input_reference[]=@/path/to/last_frame.jpg"
        ```


        ### 首尾帧 15s · 图片 URL

        ```bash

        curl -X POST "https://api.example.com/v1/videos" \
          -H "Authorization: Bearer YOUR_API_KEY" \
          -F "model=veo_3_1-fast-fl-remix" \
          -F "prompt=广告产品展示" \
          -F "prompt_extend=产品旋转展示细节，背景渐变" \
          -F "size=1280x720" \
          -F "input_reference[]=https://example.com/first.png" \
          -F "input_reference[]=https://example.com/last.jpg"
        ```


        ### 参考图 15s · 多张参考图

        ```bash

        curl -X POST "https://api.example.com/v1/videos" \
          -H "Authorization: Bearer YOUR_API_KEY" \
          -F "model=veo_3_1-fast-remix" \
          -F "prompt=根据参考图生成视频" \
          -F "prompt_extend=视频继续，场景自然过渡" \
          -F "size=1280x720" \
          -F "input_reference[]=@/path/to/ref1.jpg" \
          -F "input_reference[]=@/path/to/ref2.jpg" \
          -F "input_reference[]=@/path/to/ref3.jpg"
        ```


        ### Python 示例

        ```python

        import requests


        url = "https://api.example.com/v1/videos"


        headers = {
            "Authorization": "Bearer YOUR_API_KEY"
        }


        files = [
            ("model", (None, "veo_3_1-fast-fl-remix")),
            ("size", (None, "1080x1920")),
            ("prompt", (None, "产品广告展示")),
            ("prompt_extend", (None, "产品旋转，展示更多细节")),
            ("input_reference[]", (None, "https://example.com/first.png")),
            ("input_reference[]", (None, "https://example.com/last.jpg")),
        ]


        response = requests.post(url, headers=headers, files=files)


        print(response.status_code)

        print(response.text)

        ```


        ---


        ## 响应说明


        提交和查询接口返回业务数据位于 `data` 字段中。


        ### 外层字段


        | 参数名 | 类型 | 说明 |

        |--------|------|------|

        | id | number | NewAPI 任务自增ID |

        | task_id | string | NewAPI 任务ID，用于查询任务状态 |

        | status | string | NewAPI
        状态：`SUBMITTED`、`IN_PROGRESS`、`SUCCESS`、`FAILURE` |

        | progress | string | 进度百分比，如 `"61%"` |

        | fail_reason | string | 成功时为视频下载地址，失败时为失败原因 |

        | result_url | string | 成功时的视频下载地址（仅 SUCCESS 状态） |

        | data | object | **业务数据（以下为 data 内字段）** |


        ### data 内字段


        | 参数名 | 类型 | 说明 |

        |--------|------|------|

        | id | string | 中间件任务ID |

        | object | string | 对象类型，固定值：`video` |

        | model | string | 使用的模型名称 |

        | status | string |
        任务状态：`queued`（排队中）、`processing`（处理中）、`completed`（已完成）、`failed`（失败） |

        | progress | number | 任务进度，0-100 |

        | created_at | number | 创建时间戳（秒） |

        | completed_at | number | 完成时间戳（秒，仅 completed 状态返回） |

        | video_url | string | 最终 15s 视频地址（completed 时为 15s 视频；extend_failed
        时为可用的 8s 视频） |

        | first_video_url | string | 前 8 秒视频地址（仅 completed 状态返回） |

        | remix_id | string | 第一段视频的上游任务ID，提交成功后始终返回，可用于手动二创重试 |

        | remix_id_extend | string | 二创延长的上游任务ID，二创阶段开始后始终返回（不论成功或失败） |

        | error | object | 错误信息（仅 failed 状态返回），含 `code` 和 `message` 字段 |


        ## 响应示例


        ### 生成中（IN_PROGRESS）

        ```json

        {
          "id": 1235905,
          "created_at": 1777175740,
          "updated_at": 1777175888,
          "task_id": "task_zgUBKXVW6YhJkXPvuTJ2Y0jaLnycfEu9",
          "platform": "1",
          "user_id": 2,
          "channel_id": 7,
          "quota": 425000,
          "action": "textGenerate",
          "status": "IN_PROGRESS",
          "fail_reason": "",
          "submit_time": 1777175740,
          "start_time": 1777175789,
          "finish_time": 0,
          "progress": "61%",
          "properties": {
            "upstream_model_name": "veo_3_1-fast-remix",
            "origin_model_name": "veo_3_1-fast-remix"
          },
          "data": {
            "id": "task_Dg8gD60Ntv0QgabS5jmGY6IwgraflRXo",
            "model": "veo_3_1-fast-remix",
            "object": "video",
            "status": "processing",
            "progress": 61,
            "remix_id": "video_08a9eb19-2ea9-4753-8fde-4ae1b0867952",
            "created_at": 1777175740,
            "remix_id_extend": "video_e8fb1fff-cf79-431d-8c57-9c87e8d36fd0"
          }
        }

        ```


        > `progress` 0-49 表示第一段视频生成中，50-99 表示二创延长中。`remix_id_extend` 在二创阶段开始后出现。


        ### 任务完成（SUCCESS / 15 秒视频）

        ```json

        {
          "id": 1235905,
          "created_at": 1777175740,
          "updated_at": 1777176026,
          "task_id": "task_zgUBKXVW6YhJkXPvuTJ2Y0jaLnycfEu9",
          "platform": "1",
          "user_id": 2,
          "channel_id": 7,
          "quota": 425000,
          "action": "textGenerate",
          "status": "SUCCESS",
          "fail_reason": "https://xxx.com/v1/videos/task_Dg8gD60Ntv0QgabS5jmGY6IwgraflRXo/content",
          "result_url": "https://xxx.com/v1/videos/task_Dg8gD60Ntv0QgabS5jmGY6IwgraflRXo/content",
          "submit_time": 1777175740,
          "start_time": 1777175789,
          "finish_time": 1777175907,
          "progress": "100%",
          "properties": {
            "upstream_model_name": "veo_3_1-fast-remix",
            "origin_model_name": "veo_3_1-fast-remix"
          },
          "data": {
            "id": "task_Dg8gD60Ntv0QgabS5jmGY6IwgraflRXo",
            "model": "veo_3_1-fast-remix",
            "object": "video",
            "status": "completed",
            "progress": 100,
            "remix_id": "video_08a9eb19-2ea9-4753-8fde-4ae1b0867952",
            "video_url": "https://videos-us3.ss2.life/extend/xxxxx175907133_3bd6883e.mp4",
            "created_at": 1777175740,
            "completed_at": 1777175907,
            "first_video_url": "https://videos-us3.ss2.life/video/a8a0f0cb-7983-4ea2-9b55-5785b983b8da?Expires=...",
            "remix_id_extend": "video_e8fb1fff-cf79-431d-8c57-9c87e8d36fd0"
          }
        }

        ```


        > - `data.video_url`：15 秒完整视频（存储在中间件服务器）

        > - `data.first_video_url`：前 8 秒视频（上游直链）

        > - `data.remix_id`：第一段视频的上游ID（始终返回）

        > - `data.remix_id_extend`：二创任务的上游ID（始终返回）


        ### 延长失败（前 8 秒可用）

        ```json

        {
          "id": 1235906,
          "task_id": "task_xxxxxxxxxxxx",
          "status": "FAILURE",
          "fail_reason": "第一段视频生成成功，但二创失败：线路繁忙，请重试 (E-2003)",
          "progress": "50%",
          "data": {
            "id": "task_yyyyyyyyyyyy",
            "model": "veo_3_1-fast-remix",
            "object": "video",
            "status": "failed",
            "progress": 50,
            "created_at": 1777175740,
            "error": {
              "code": "extend_failed",
              "message": "第一段视频生成成功，但二创失败：线路繁忙，请重试 (E-2003)"
            },
            "video_url": "https://videos-us3.ss2.life/video/a8a0f0cb-xxxx-xxxx",
            "remix_id": "video_08a9eb19-xxxx-xxxx",
            "remix_id_extend": "video_e8fb1fff-xxxx-xxxx"
          }
        }

        ```


        > 当 `data.error.code` 为 `extend_failed` 时，`data.video_url` 是可用的前 8
        秒视频。`remix_id` 可用于手动重试二创延长。


        ### 生成失败（第一段即失败）

        ```json

        {
          "id": 1235907,
          "task_id": "task_xxxxxxxxxxxx",
          "status": "FAILURE",
          "fail_reason": "视频生成失败：违反谷歌AI安全协议 请调整图片和提示词 (E-1005)",
          "progress": "0%",
          "data": {
            "id": "task_zzzzzzzzzzzz",
            "model": "veo_3_1-fast-remix",
            "object": "video",
            "status": "failed",
            "progress": 0,
            "created_at": 1777175740,
            "error": {
              "code": "generate_failed",
              "message": "视频生成失败：违反谷歌AI安全协议 请调整图片和提示词 (E-1005)"
            },
            "remix_id": "video_xxxxxxxx-xxxx-xxxx"
          }
        }

        ```


        > 第一段生成就失败时，没有 `video_url`、`first_video_url` 和 `remix_id_extend`。仅返回
        `remix_id`。


        ---


        ## 查询任务状态


        ### 接口地址

        `GET /v1/videos/{task_id}`


        ### 请求示例

        ```bash

        curl -X GET
        "https://api.example.com/v1/videos/task_zgUBKXVW6YhJkXPvuTJ2Y0jaLnycfEu9"
        \
          -H "Authorization: Bearer YOUR_API_KEY"
        ```


        ### 响应参数

        与提交接口响应结构相同。


        ---


        ## 字段返回规则汇总


        | 字段 | queued / processing | completed | extend_failed | generate_failed
        |

        |------|:-------------------:|:---------:|:-------------:|:---------------:|

        | remix_id | 有（第一段提交后） | 有 | 有 | 有 |

        | remix_id_extend | 有（二创开始后） | 有 | 有 | 无 |

        | video_url | 无 | 15s 视频 | 8s 视频 | 无 |

        | first_video_url | 无 | 8s 视频 | 无 | 无 |

        | error | 无 | 无 | 有 | 有 |


        ---


        ## 注意事项


        1. **两段提示词**：`prompt` 控制前 8 秒内容，`prompt_extend` 控制后 7 秒延长内容，请分别描述。


        2. **仅 multipart**：`POST /v1/videos` 的业务参数请使用 **form-data**；不要使用 JSON
        body。


        3. **size 尺寸参数**：
           - 格式为 `widthxheight`，如 `1280x720`、`1920x1080`
           - **宽大于高**为横屏（16:9），**高大于宽**为竖屏（9:16）
           - 推荐：`1280x720`（横屏 720p）、`720x1280`（竖屏 720p）、`1920x1080`（横屏 1080p）、`1080x1920`（竖屏 1080p）

        4. **input_reference[]**：
           - 字段名必须为 **`input_reference[]`**（含方括号）
           - 多图 = 多个同名字段
           - 首尾帧模式需保证图片顺序（第 1 张=首帧，第 2 张=尾帧）

        5. **模型选择**：
           - **文生视频 / 参考图**：使用不含 `-fl` 的模型（如 `veo_3_1-fast-remix`、`veo_3_1-remix`），参考图模式传 `input_reference[]`，文生视频不传
           - **首尾帧**：使用含 `-fl` 的模型（如 `veo_3_1-fast-fl-remix`、`veo_3_1-fl-remix`），传 1～2 张图
           - 高清版在模型名中含 `-hd`，如 `veo_3_1-fast-hd-remix`、`veo_3_1-fast-fl-hd-remix`

        6. **URL 说明**：图片请使用**直链**（返回图片二进制），不要传 HTML 网页地址。


        7. **异步**：提交成功仅返回任务 ID，须轮询 `GET /v1/videos/{task_id}` 获取进度与结果。


        8. **失败降级**：当 `data.error.code` 为 `extend_failed` 时，表示前 8
        秒视频已生成成功但延长失败。此时 `data.video_url` 包含可用的 8 秒视频，`data.remix_id`
        可用于后续手动重试延长。


        9. **生成耗时**：15 秒视频需要依次完成两段生成，总耗时约为单段的 2 倍，请适当增大轮询等待时间。


        10. **remix_id 与 remix_id_extend**：`remix_id`
        在第一段视频提交成功后始终返回；`remix_id_extend` 在二创阶段开始后始终返回，无论最终成功或失败。两个 ID
        均可用于手动操作或排查问题。
      tags:
        - 失效接口
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
                  description: 文生视频和参考图模式，必须加-remix，才能15s，否则就是8s
                  example: veo_3_1-fast-remix
                  type: string
                prompt:
                  description: 前8s的提示词
                  example: 广告
                  type: string
                prompt_extend:
                  description: 后7s的提示词
                  example: ''
                  type: string
                size:
                  example: 1920x1080
                  type: string
                input_reference:
                  format: binary
                  type: string
                  example: MA==/logo.png
              required:
                - model
                - prompt
                - prompt_extend
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
                      upstream_model_name:
                        type: string
                      origin_model_name:
                        type: string
                    required:
                      - upstream_model_name
                      - origin_model_name
                    x-apifox-orders:
                      - upstream_model_name
                      - origin_model_name
                  data:
                    type: object
                    properties:
                      id:
                        type: string
                      model:
                        type: string
                      object:
                        type: string
                      status:
                        type: string
                      progress:
                        type: integer
                      remix_id:
                        type: string
                      video_url:
                        type: string
                      created_at:
                        type: integer
                      completed_at:
                        type: integer
                      first_video_url:
                        type: string
                      remix_id_extend:
                        type: string
                    required:
                      - id
                      - model
                      - object
                      - status
                      - progress
                      - remix_id
                      - video_url
                      - created_at
                      - completed_at
                      - first_video_url
                      - remix_id_extend
                    x-apifox-orders:
                      - id
                      - model
                      - object
                      - status
                      - progress
                      - remix_id
                      - video_url
                      - created_at
                      - completed_at
                      - first_video_url
                      - remix_id_extend
                  object:
                    type: string
                  model:
                    type: string
                  completed_at:
                    type: integer
                  size:
                    type: string
                required:
                  - id
                  - created_at
                  - updated_at
                  - task_id
                  - platform
                  - user_id
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
                  - data
                  - object
                  - model
                  - completed_at
                  - size
                x-apifox-orders:
                  - id
                  - created_at
                  - updated_at
                  - task_id
                  - platform
                  - user_id
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
                  - data
                  - object
                  - model
                  - completed_at
                  - size
              example:
                id: 1235905
                created_at: 1777175740
                updated_at: 1777176026
                task_id: task_zgUBKXVW6YhJkXPvuTJ2Y0jaLnycfEu9
                platform: '1'
                user_id: 2
                channel_id: 7
                quota: 425000
                action: textGenerate
                status: SUCCESS
                fail_reason: >-
                  https://xxx.com/v1/videos/task_Dg8gD60Ntv0QgabS5jmGY6IwgraflRXo/content
                result_url: >-
                  https://xxx.com/v1/videos/task_Dg8gD60Ntv0QgabS5jmGY6IwgraflRXo/content
                submit_time: 1777175740
                start_time: 1777175789
                finish_time: 1777175907
                progress: 100%
                properties:
                  upstream_model_name: veo_3_1-fast-remix
                  origin_model_name: veo_3_1-fast-remix
                data:
                  id: task_Dg8gD60Ntv0QgabS5jmGY6IwgraflRXo
                  model: veo_3_1-fast-remix
                  object: video
                  status: completed
                  progress: 100
                  remix_id: video_08a9eb19-2ea9-4753-8fde-4ae1b0867952
                  video_url: >-
                    https://videos-us3.ss2.life/extend/xxxxx175907133_3bd6883e.mp4
                  created_at: 1777175740
                  completed_at: 1777175907
                  first_video_url: >-
                    https://videos-us3.ss2.life/video/a8a0f0cb-7983-4ea2-9b55-5785b983b8da?Expires=...
                  remix_id_extend: video_e8fb1fff-cf79-431d-8c57-9c87e8d36fd0
          headers: {}
          x-apifox-name: 成功
      security: []
      x-apifox-folder: 失效接口
      x-apifox-status: developing
      x-run-in-apifox: https://app.apifox.com/web/project/7902379/apis/api-449549907-run
components:
  schemas: {}
  securitySchemes: {}
servers: []
security: []

```
