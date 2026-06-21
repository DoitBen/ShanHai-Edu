# sora视频接口

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
      summary: sora视频接口
      deprecated: false
      description: >
        # Sora视频生成接口文档


        ## 接口地址

        `POST /v1/videos`


        ## 功能说明

        支持Sora模型的文生视频和图生视频


        ## 请求头


        | 参数名 | 类型 | 必填 | 说明 |

        |--------|------|------|------|

        | Authorization | string | 是 | Bearer YOUR_API_KEY |

        | Content-Type | string | 推荐 | application/json（文生视频或图生视频使用URL）或
        multipart/form-data（图生视频使用文件） |


        ## 请求参数


        ### 文生视频


        | 参数名 | 类型 | 必填 | 说明 |

        |--------|------|------|------|

        | model | string | 是 | 模型名称，详见下方模型列表 |

        | prompt | string | 是 | 文本提示词 |

        | style | string | 否 | 视频风格 |


        ### 图生视频


        图生视频支持两种方式提交参考图片：


        **方式一：使用图片 URL（推荐）**

        - Content-Type: `application/json`

        - 使用 `image_url` 参数传递可访问的图片 URL


        | 参数名 | 类型 | 必填 | 说明 |

        |--------|------|------|------|

        | model | string | 是 | 模型名称 |

        | prompt | string | 是 | 文本提示词 |

        | image_url | string | 是 | 参考图片 URL（需要可以访问的图片地址） |

        | style | string | 否 | 视频风格 |


        **方式二：使用图片文件**

        - Content-Type: `multipart/form-data`（必填）

        - 使用 `input_reference` 字段上传图片文件


        | 参数名 | 类型 | 必填 | 说明 |

        |--------|------|------|------|

        | model | string | 是 | 模型名称，例如：sora-2-portrait-15s |

        | prompt | string | 是 | 文本提示词 |

        | input_reference | File | 是 | 参考图片文件 |

        | style | string | 否 | 视频风格 |


        **注意**：`image_url` 和 `input_reference` 二选一，不能同时使用


        ## 支持的模型


        | 模型名称 | 说明 |

        |---------|------|

        | sora-2-landscape-10s | Sora 2 横屏 10秒 |

        | sora-2-portrait-10s | Sora 2 竖屏 10秒 |

        | sora-2-landscape-15s | Sora 2 横屏 15秒 |

        | sora-2-portrait-15s | Sora 2 竖屏 15秒 |

        | sora-2-pro-landscape-25s | Sora 2 Pro 横屏 25秒 |

        | sora-2-pro-portrait-25s | Sora 2 Pro 竖屏 25秒 |

        | sora-2-pro-landscape-hd-15s | Sora 2 Pro 横屏 HD 15秒 |

        | sora-2-pro-portrait-hd-15s | Sora 2 Pro 竖屏 HD 15秒 |


        ## 请求示例


        ### 文生视频

        ```bash

        curl -X POST https://otuapi.com/v1/videos \
          -H "Authorization: Bearer YOUR_API_KEY" \
          -H "Content-Type: application/json" \
          -d '{
            "model": "sora-2-landscape-10s",
            "prompt": "一只可爱的小猫在花园里玩耍"
          }'
        ```


        ### 图生视频


        **方式一：使用图片 URL（推荐）**

        ```bash

        curl -X POST https://otuapi.com/v1/videos \
          -H "Authorization: Bearer YOUR_API_KEY" \
          -H "Content-Type: application/json" \
          -d '{
            "model": "sora-2-portrait-10s",
            "prompt": "宣传片",
            "image_url": "https://www.baidu.com/img/PCtm_d9c8750bed0b3c7d089fa7d55720d6cf.png"
          }'
        ```


        **方式二：使用图片文件**

        ```bash

        curl -X POST https://otuapi.com/v1/videos \
          -H "Authorization: Bearer YOUR_API_KEY" \
          -F "model=sora-2-portrait-15s" \
          -F "prompt=让这张图片动起来" \
          -F "input_reference=@/path/to/image.jpg"
        ```


        ## 响应参数


        | 参数名 | 类型 | 说明 |

        |--------|------|------|

        | id | string | 任务ID |

        | object | string | 对象类型，固定值：video |

        | model | string | 使用的模型名称 |

        | status | string |
        任务状态：queued（排队中）、processing（处理中）、completed（已完成）、failed（失败） |

        | progress | number | 任务进度，0-100 |

        | created_at | number | 创建时间戳（秒） |

        | completed_at | number | 完成时间戳（秒，仅completed状态返回） |


        ## 响应示例


        ### 提交成功（排队中）

        ```json

        {
          "id": "task_xxxxxxxxxxxxx",
          "object": "video",
          "model": "sora-2-landscape-10s",
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
          "model": "sora-2-landscape-10s",
          "status": "completed",
          "progress": 100,
          "created_at": 1709876543,
          "completed_at": 1709876600
        }

        ```


        ## 查询任务状态


        ### 接口地址

        `GET /v1/videos/{task_id}`


        ### 请求示例

        ```bash

        curl -X GET https://otuapi.com/v1/videos/task_xxxxxxxxxxxxx \
          -H "Authorization: Bearer YOUR_API_KEY"
        ```


        ### 响应参数

        与提交接口响应参数相同，完成后会包含视频URL




        ## 注意事项


        1. **文生视频**：使用 `application/json` 格式提交

        2. **图生视频**：支持两种方式
           - **使用图片 URL**：使用 `application/json` 格式，通过 `image_url` 参数传递可访问的图片 URL（推荐）
           - **使用图片文件**：使用 `multipart/form-data` 格式，通过 `input_reference` 字段上传图片文件
           - `image_url` 和 `input_reference` 二选一，不能同时使用
        3. **异步处理**：接口返回任务ID后，需要通过轮询 `GET /v1/videos/{task_id}` 查询任务进度和结果

        4. **图片 URL 要求**：`image_url` 必须是可公开访问的图片地址，支持常见的图片格式（jpg、png、webp 等）
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
          required: true
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
                  description: 模型名称
                prompt:
                  type: string
                  description: 提示词
              required:
                - model
                - prompt
              x-apifox-orders:
                - model
                - prompt
            example:
              model: sora-2-landscape-10s
              prompt: 一只可爱的小猫在花园里玩耍
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
      x-apifox-folder: 失效接口
      x-apifox-status: developing
      x-run-in-apifox: https://app.apifox.com/web/project/7902379/apis/api-424645155-run
components:
  schemas: {}
  securitySchemes: {}
servers: []
security: []

```
