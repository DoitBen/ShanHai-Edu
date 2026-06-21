# Omni创建

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
      summary: Omni创建
      deprecated: false
      description: >-
        # Omni 视频生成接口文档


        ## 接口地址

        `POST /v1/videos`


        ## 功能说明


        支持 Omni 系列模型的文生视频、图生视频和视频修改：


        - **文生视频**：不传图片，仅用提示词生成

        - **图生视频（参考图模式）**：支持最多 **7 张**参考图片

        - **视频修改**：将视频文件或视频 URL 通过图片字段传入（表单用 `input_reference` 传文件，JSON 用
        `images` 传 URL），配合提示词对视频进行修改


        > **暂不支持首尾帧模式。**


        ### 当前可用模型


        | 模型名 | 时长 | 分辨率 | 说明 |

        |--------|------|--------|------|

        | `omni_flash-10s` | 10s | 720p | 横竖屏均支持 |


        > 后续将陆续新增更多档位（更高分辨率、更长时长等），字段用法不变。


        ---


        ## 请求方式


        支持两种方式，**任选其一**：


        | 方式 | Content-Type | 图生视频时的图片字段 |

        |------|--------------|----------------------|

        | **multipart/form-data** | `multipart/form-data` | 使用
        **`input_reference`**（可重复字段，每张图一个字段） |

        | **application/json** | `application/json` | 使用
        **`images`**（字符串数组，每项对应一张图）；**不得**在 JSON 中使用 `input_reference` |


        ---


        ## 请求头


        | 参数名 | 类型 | 必填 | 说明 |

        |--------|------|------|------|

        | Authorization | string | 是 | `Bearer YOUR_API_KEY` |

        | Content-Type | string | 是 | `multipart/form-data` 或
        `application/json`，须与请求体一致 |


        ---


        ## 表单字段说明


        | 参数名 | 类型 | 必填 | 说明 |

        |--------|------|------|------|

        | model | string | 是 | 模型名称，如 `omni_flash-10s`（详见上方模型表） |

        | prompt | string | 是 | 文本提示词 |

        | size | string | 否 | 视频尺寸，格式 `widthxheight`，如
        `1280x720`、`720x1280`（详见注意事项） |

        | input_reference | 可重复 | 否 |
        图生视频或视频修改时传递，**同一字段名可重复多次**，每次对应一张图或一个视频文件，最多 7
        项。文生视频不传本字段。**传视频文件时**，以本地文件方式提交视频，配合提示词对其进行修改。 |


        ### `input_reference` 的传法


        | 方式 | 说明 |

        |------|------|

        | **本地文件（图片）** | multipart 里以文件部件提交，例如 `-F
        "input_reference=@/path/to/image.jpg"` |

        | **本地文件（视频）** | multipart 里以文件部件提交视频，例如 `-F
        "input_reference=@/path/to/video.mp4"` |

        | **图片 URL** | 以普通表单文本提交**可公网访问的图片直链**，例如 `-F
        "input_reference=https://example.com/a.png"`（勿传需登录的短链页面） |

        | **Base64** | 以文本字段提交完整 data URI，例如 `-F
        "input_reference=data:image/jpeg;base64,/9j/4AAQSkZJRg..."` |


        > 传入图片 URL 时，网关会自动将其下载并转为 Base64 后发给上游，请确保 URL 为**可公网访问的图片直链**。


        **顺序约定**：参考图按传入顺序作为参考图 1、2……7，最多 7 张。


        ---


        ## JSON 请求体说明（`application/json`）


        | 参数名 | 类型 | 必填 | 说明 |

        |--------|------|------|------|

        | model | string | 是 | 与表单一致，如 `omni_flash-10s` |

        | prompt | string | 是 | 文本提示词 |

        | size | string | 否 | 视频尺寸，格式 `widthxheight`，如 `1280x720` |

        | images | string[] | 否 | **图生视频或视频修改时传**：每项为一张图或一个视频（URL / Base64 data
        URI），最多 7 项。**修改视频时传视频 URL**（不支持直接传视频文件，须使用可公网访问的视频直链）。文生视频不传或传
        `[]`。**禁止使用** `input_reference`。 |


        ### `images` 每项取值


        | 方式 | JSON `images` 数组元素 |

        |------|------------------------|

        | **图片 URL** | `"https://example.com/a.png"`（须为可公网访问的图片直链） |

        | **视频 URL** | `"https://example.com/video.mp4"`（须为可公网访问的视频直链，用于视频修改） |

        | **Base64** | `"data:image/jpeg;base64,/9j/4AAQSkZJRg..."`（完整 data URI）
        |

        | **本地文件** | JSON 无法直接附带文件，请先读取为字节后编码为 data URI 字符串写入
        `images`；**视频修改建议改用表单方式传本地视频文件** |


        ---


        ## 请求示例


        ### 文生视频（JSON）


        ```bash

        curl -X POST "https://xxxxx.com/v1/videos" \
          -H "Authorization: Bearer YOUR_API_KEY" \
          -H "Content-Type: application/json" \
          -d '{
            "model": "omni_flash-10s",
            "prompt": "一只可爱的小猫在花园里玩耍",
            "size": "1280x720"
          }'
        ```


        ### 文生视频（表单）


        ```bash

        curl -X POST "https://xxxxx.com/v1/videos" \
          -H "Authorization: Bearer YOUR_API_KEY" \
          -F "model=omni_flash-10s" \
          -F "prompt=一只可爱的小猫在花园里玩耍" \
          -F "size=1280x720"
        ```


        ### 图生视频 · 参考图 · URL 传图（JSON）


        ```bash

        curl -X POST "https://xxxxx.com/v1/videos" \
          -H "Authorization: Bearer YOUR_API_KEY" \
          -H "Content-Type: application/json" \
          -d '{
            "model": "omni_flash-10s",
            "prompt": "根据参考图生成视频",
            "size": "1280x720",
            "images": [
              "https://example.com/image1.jpg",
              "https://example.com/image2.jpg",
              "https://example.com/image3.jpg"
            ]
          }'
        ```


        ### 图生视频 · 参考图 · URL 传图（表单）


        ```bash

        curl -X POST "https://xxxxx.com/v1/videos" \
          -H "Authorization: Bearer YOUR_API_KEY" \
          -F "model=omni_flash-10s" \
          -F "prompt=根据参考图生成视频" \
          -F "size=1280x720" \
          -F "input_reference=https://example.com/image1.jpg" \
          -F "input_reference=https://example.com/image2.jpg" \
          -F "input_reference=https://example.com/image3.jpg"
        ```


        Windows cmd 示例（`curl.exe` 使用 `^` 换行）：


        ```bat

        curl.exe -X POST "https://xxxxx.com/v1/videos" ^
          -H "Authorization: Bearer YOUR_API_KEY" ^
          -F "model=omni_flash-10s" ^
          -F "prompt=根据参考图生成视频" ^
          -F "size=1280x720" ^
          -F "input_reference=https://example.com/image1.jpg" ^
          -F "input_reference=https://example.com/image2.jpg"
        ```


        ### 图生视频 · 参考图 · 本地文件（表单，最多 7 张）


        ```bash

        curl -X POST "https://xxxxx.com/v1/videos" \
          -H "Authorization: Bearer YOUR_API_KEY" \
          -F "model=omni_flash-10s" \
          -F "prompt=根据参考图生成视频" \
          -F "size=1280x720" \
          -F "input_reference=@/path/to/ref1.jpg" \
          -F "input_reference=@/path/to/ref2.jpg" \
          -F "input_reference=@/path/to/ref3.jpg"
        ```


        ### Python 示例（表单）


        ```python

        import requests


        url = "https://xxxxx.com/v1/videos"


        headers = {
            "Authorization": "Bearer YOUR_API_KEY"
        }


        # multipart/form-data，图生视频示例

        files = [
            ("model",  (None, "omni_flash-10s")),
            ("prompt", (None, "根据参考图生成视频")),
            ("size",   (None, "1280x720")),

            # 最多 7 张参考图，每张一个 input_reference
            ("input_reference", (None, "https://example.com/image1.jpg")),
            ("input_reference", (None, "https://example.com/image2.jpg")),
            ("input_reference", (None, "https://example.com/image3.jpg")),
        ]


        response = requests.post(url, headers=headers, files=files)

        print(response.status_code)

        print(response.text)

        ```


        ---


        ## 响应参数


        | 参数名 | 类型 | 说明 |

        |--------|------|------|

        | id | string | 任务 ID |

        | object | string | 固定值：`video` |

        | model | string | 实际使用的模型名称 |

        | status | string |
        任务状态：`queued`（排队中）、`processing`（处理中）、`completed`（已完成）、`failed`（失败） |

        | progress | number | 任务进度，0～100 |

        | created_at | number | 创建时间戳（秒） |

        | completed_at | number | 完成时间戳（秒，仅 `completed` 状态返回） |

        | size | string | 视频尺寸 |

        | video_url | string | 视频直链（仅 `completed` 状态返回） |

        | error | object | 错误信息（仅 `failed` 状态返回），含 `message`、`code` 字段 |


        ## 响应示例


        ### 提交成功（排队中）


        ```json

        {
          "id": "task_xxxxxxxxxxxxx",
          "object": "video",
          "model": "omni_flash-10s",
          "status": "queued",
          "progress": 0,
          "created_at": 1709876543,
          "size": "1280x720"
        }

        ```


        ### 任务完成


        ```json

        {
          "id": "task_xxxxxxxxxxxxx",
          "object": "video",
          "model": "omni_flash-10s",
          "status": "completed",
          "progress": 100,
          "created_at": 1709876543,
          "completed_at": 1709876600,
          "size": "1280x720",
          "video_url": "https://example.com/output.mp4"
        }

        ```


        ### 任务失败


        ```json

        {
          "id": "task_xxxxxxxxxxxxx",
          "object": "video",
          "model": "omni_flash-10s",
          "status": "failed",
          "progress": 0,
          "created_at": 1709876543,
          "error": {
            "code": "content_policy_violation",
            "message": "内容违反使用政策"
          }
        }

        ```


        ---


        ## 查询任务状态


        ### 接口地址


        `GET /v1/videos/{task_id}`


        ### 请求示例


        ```bash

        curl -X GET "https://xxxxx.com/v1/videos/task_xxxxxxxxxxxxx" \
          -H "Authorization: Bearer YOUR_API_KEY"
        ```


        响应参数与提交接口相同，`completed` 后会包含 `video_url`。


        ---


        ## 注意事项


        1. **模型名即完整规格**：模型名中已包含时长和分辨率信息（如 `omni_flash-10s` 表示 flash 质量 10 秒
        720p）。


        2. **size 尺寸参数**：
           - 格式为 `widthxheight`，如 `1280x720`、`720x1280`
           - **宽大于高**为横屏（16:9），**高大于宽**为竖屏（9:16）
           - 推荐值：`1280x720`（横屏 720p）、`720x1280`（竖屏 720p）
           - 后续高清模型推荐：`1920x1080`（横屏）、`1080x1920`（竖屏）

        3. **参考图/视频上限为 7 项**：`input_reference`（表单）或 `images`（JSON）最多传 7
        项，超出部分会被忽略或报错。**文件数量越多、单个文件越大，上传耗时越长，请耐心等待。**


        4. **视频修改传参规则**：表单（`multipart/form-data`）用 `input_reference`
        传**本地视频文件**；JSON（`application/json`）用 `images` 传**视频
        URL**（须为可公网访问的视频直链）。不支持在 JSON 中直接附带视频文件，如需传本地视频请使用表单方式。


        5. **JSON 与表单二选一**：`application/json` 时图片必须用 `images` 数组，**不要**写
        `input_reference`；`multipart/form-data` 时用重复的 `input_reference` 字段。


        6. **图片/视频 URL 要求**：须为**直链**（直接返回文件二进制内容），不要传网页 HTML 地址或需要登录才能访问的链接。


        7. **暂不支持首尾帧**：Omni 系列当前只支持文生视频和参考图模式，首尾帧模式不支持。


        8. **异步接口**：提交成功仅返回任务 ID，需轮询 `GET /v1/videos/{task_id}` 获取进度与结果。
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
          example: application/json
          schema:
            type: string
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                model:
                  type: string
                  description: 模型
                prompt:
                  type: string
                  description: 提示词
                size:
                  type: string
                  description: 尺寸
                input_reference:
                  type: string
                  description: 图生视频传图
              required:
                - model
                - prompt
              x-apifox-orders:
                - model
                - prompt
                - size
                - input_reference
            example:
              model: omni_flash-10s
              prompt: 广告
              size: 1280x720
              images:
                - https://xxxxxxxx.jpg
                - https://xxxxxxxx.png
      responses:
        '200':
          description: ''
          content:
            application/json:
              schema:
                type: object
                properties:
                  id:
                    type: string
                  object:
                    type: string
                  model:
                    type: string
                  status:
                    type: string
                  progress:
                    type: integer
                  created_at:
                    type: integer
                  completed_at:
                    type: integer
                  size:
                    type: string
                required:
                  - id
                  - object
                  - model
                  - status
                  - progress
                  - created_at
                  - completed_at
                  - size
                x-apifox-orders:
                  - id
                  - object
                  - model
                  - status
                  - progress
                  - created_at
                  - completed_at
                  - size
              example:
                id: task_xxxxxxxxxxxxx
                object: video
                model: veo_3_1-fast
                status: completed
                progress: 100
                created_at: 1709876543
                completed_at: 1709876600
                size: 1920x1080
          headers: {}
          x-apifox-name: 成功
      security: []
      x-apifox-folder: 视频生成（Videos）
      x-apifox-status: developing
      x-run-in-apifox: https://app.apifox.com/web/project/7902379/apis/api-462450037-run
components:
  schemas: {}
  securitySchemes: {}
servers: []
security: []

```
