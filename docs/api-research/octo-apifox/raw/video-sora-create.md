# sora创建

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
      summary: sora创建
      deprecated: false
      description: >-
        # Sora视频生成接口文档（时长扩展版）


        ## 接口地址

        `POST /v1/videos`


        ## 功能说明

        支持 Sora 2 时长扩展模型的文生视频和图生视频，时长直接体现在模型名中（12 秒 ），方向由 `size` 决定。


        ## 请求头


        | 参数名 | 类型 | 必填 | 说明 |

        |--------|------|------|------|

        | Authorization | string | 是 | Bearer YOUR_API_KEY |

        | Content-Type | string | 推荐 | application/json或 multipart/form-data |


        ## 请求参数


        ### 文生视频


        | 参数名 | 类型 | 必填 | 说明 |

        |--------|------|------|------|

        | model | string | 是 | 模型名称，详见下方模型列表（如 `sora-2-12s`） |

        | prompt | string | 是 | 文本提示词 |

        | size | string | 是 | 画面尺寸，宽>高为横屏，高>宽为竖屏，如
        `1920x1080`（横屏）、`1080x1920`（竖屏） |


        ### 图生视频


        图生视频支持两种方式提交参考图片：


        **方式一：使用图片 URL（推荐）**

        - Content-Type: `application/json`

        - 使用 `images` 参数传递可访问的图片 URL 数组


        | 参数名 | 类型 | 必填 | 说明 |

        |--------|------|------|------|

        | model | string | 是 | 模型名称（如 `sora-2-12s`） |

        | prompt | string | 是 | 文本提示词 |

        | images | array | 是 | 参考图片 URL 数组（需要可以访问的图片地址，取第一张） |

        | size | string | 是 | 画面尺寸，宽>高为横屏，高>宽为竖屏，如
        `1920x1080`（横屏）、`1080x1920`（竖屏） |


        **方式二：使用图片文件**

        - Content-Type: `multipart/form-data`（必填）

        - 使用 `input_reference` 字段上传图片文件


        | 参数名 | 类型 | 必填 | 说明 |

        |--------|------|------|------|

        | model | string | 是 | 模型名称（如 `sora-2-12s`） |

        | prompt | string | 是 | 文本提示词 |

        | input_reference | File | 是 | 参考图片文件 |

        | size | string | 是 | 画面尺寸，宽>高为横屏，高>宽为竖屏，如
        `1920x1080`（横屏）、`1080x1920`（竖屏） |


        **注意**：`images` 和 `input_reference` 二选一，不能同时使用。


        ## 支持的模型


        | 模型名称 | 时长 | 说明 |

        |---------|------|------|

        | sora-2-12s | 12 秒 | Sora 2 （横竖屏由 size 决定） |



        ## 请求示例


        ### 文生视频

        ```bash

        curl -X POST https://xxx.com/v1/videos \
          -H "Authorization: Bearer YOUR_API_KEY" \
          -H "Content-Type: application/json" \
          -d '{
            "model": "sora-2-12s",
            "prompt": "做个广告",
            "size": "1920x1080"
          }'
        ```


        ### 图生视频


        **方式一：使用图片 URL（推荐）**

        ```bash

        curl -X POST https://xxx.com/v1/videos \
          -H "Authorization: Bearer YOUR_API_KEY" \
          -H "Content-Type: application/json" \
          -d '{
            "model": "sora-2-12s",
            "prompt": "做个广告",
            "size": "1920x1080",
            "images": ["https://www.baidu.com/img/PCtm_d9c8750bed0b3c7d089fa7d55720d6cf.png"]
          }'
        ```


        **方式二：使用图片文件**

        ```bash

        curl -X POST https://xxx.com/v1/videos \
          -H "Authorization: Bearer YOUR_API_KEY" \
          -F "model=sora-2-12s" \
          -F "prompt=让这张图片动起来" \
          -F "size=1080x1920" \
          -F "input_reference=@/path/to/image.jpg"
        ```


        ## 响应参数


        | 参数名 | 类型 | 说明 |

        |--------|------|------|

        | id | string | 任务 ID |

        | object | string | 对象类型，固定值：`video` |

        | model | string | 使用的模型名称（可能为上游内部物理模型名，例如 `sora-2-2`，仅供参考；客户端应以提交时的
        model 为准） |

        | status | string | 任务状态：queued（排队中）、in_progress /
        processing（处理中）、completed（已完成）、failed（失败） |

        | progress | number | 任务进度，0-100 |

        | created_at | number | 创建时间戳（秒） |

        | completed_at | number | 完成时间戳（秒，仅 completed 状态返回） |

        | video_url | string | 完成后的视频地址（仅 completed 状态返回） |


        ## 响应示例


        ### 提交成功（排队中）

        ```json

        {
          "id": "task_xxxxxxxxxxxxx",
          "object": "video",
          "model": "sora-2-12s",
          "status": "queued",
          "progress": 0,
          "created_at": 1709876543
        }

        ```


        ### 任务完成

        ```json

        {
          "id": "task_xxxxxxxxxxxxx",
          "object": "video",
          "model": "sora-2-12s",
          "status": "completed",
          "progress": 100,
          "created_at": 1709876543,
          "completed_at": 1709876600,
          "video_url": "https://videos-us3.ss2.life/files/b/xxxxxx.mp4"
        }

        ```


        ## 查询任务状态


        ### 接口地址

        `GET /v1/videos/{task_id}`


        ### 请求示例

        ```bash

        curl -X GET https://xxx.com/v1/videos/task_xxxxxxxxxxxxx \
          -H "Authorization: Bearer YOUR_API_KEY"
        ```


        ### 响应参数

        与提交接口响应参数相同，完成后会包含 `video_url`。


        ## 注意事项


        1. **尺寸必须显式传入 `size`**：宽>高为横屏，高>宽为竖屏，缺省 `size` 时上游可能拒绝请求或采用未明确的默认值。

        2. **图片二选一**：`images` 与 `input_reference` 互斥；二者同时存在时行为未定义。

        3. **图片 URL 要求**：`images` 数组中的 URL 必须是可公开访问的图片地址，支持常见图片格式（jpg、png、webp
        等）。

        4. **异步处理**：接口返回任务 ID 后，需要通过轮询 `GET /v1/videos/{task_id}` 查询任务进度和结果。
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
          required: true
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
                  description: 模型
                  example: sora-2-12s
                  type: string
                prompt:
                  description: 提示词
                  example: 小猫钓鱼
                  type: string
                size:
                  description: |-
                    横竖屏
                    `16:9`（横屏）或 `9:16`（竖屏）
                  example: 1920x1080
                  type: string
                input_reference:
                  format: binary
                  type: string
                  description: 上传图片
                  example: ''
              required:
                - model
                - prompt
                - size
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
                required:
                  - id
                  - object
                  - model
                  - status
                  - progress
                  - created_at
                  - completed_at
                x-apifox-orders:
                  - id
                  - object
                  - model
                  - status
                  - progress
                  - created_at
                  - completed_at
              example:
                id: task_xxxxxxxxxxxxx
                object: video
                model: sora-2-landscape-10s
                status: completed
                progress: 100
                created_at: 1709876543
                completed_at: 1709876600
          headers: {}
          x-apifox-name: 成功
      security: []
      x-apifox-folder: 视频生成（Videos）
      x-apifox-status: developing
      x-run-in-apifox: https://app.apifox.com/web/project/7902379/apis/api-454078398-run
components:
  schemas: {}
  securitySchemes: {}
servers: []
security: []

```
