# 香蕉（异步）

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
      summary: 香蕉（异步）
      deprecated: false
      description: >
        # 图片生成接口文档


        ## 接口地址

        `POST /v1/videos`


        ## 功能说明

        支持文生图和图生图两种模式的图片生成（与视频生成共用接口，通过 `model` 参数区分）。


        ## 支持的模型


        | model 参数 | 说明 |

        |-----------|------|

        | `nano_banana_2` | 标准版，速度快 |

        | `nano_banana_pro-1K` | Pro 版，1K 分辨率 |

        | `nano_banana_pro-2K` | Pro 版，2K 分辨率 |

        | `nano_banana_pro-4K` | Pro 版，4K 分辨率 |


        ## 请求头


        | 参数名 | 类型 | 必填 | 说明 |

        |--------|------|------|------|

        | Authorization | string | 是 | Bearer YOUR_API_KEY |

        | Content-Type | string | 是 | application/json |


        ## 请求参数


        | 参数名 | 类型 | 必填 | 说明 |

        |--------|------|------|------|

        | model | string | 是 | 模型名称，如：`nano_banana_2`、`nano_banana_pro-1K` 等 |

        | prompt | string | 是 | 文本提示词，最大长度 10000 字符 |

        | aspect_ratio | string | 否 | 宽高比，可选值：`1:1`、`9:16`、`16:9`、`auto`，默认
        `auto` |

        | images | string[] | 否 | 参考图片数组（支持 Base64 或 URL），最多 5
        张。传此参数为图生图模式，不传或传空数组为文生图模式 |


        ### `images` 数组元素传法


        | 方式 | 示例 |

        |------|------|

        | **图片 URL** | `"https://example.com/reference.jpg"` |

        | **Base64** | `"data:image/jpeg;base64,/9j/4AAQSkZJRg..."` |


        > **注意**：传入图片 URL 时，网关会自动将其下载并转为 Base64 后发给上游，请确保 URL 为**可公网访问的图片直链**。


        ## 请求示例


        ### 文生图模式

        ```bash

        curl -X POST https://xxxxx.com/v1/videos \
          -H "Authorization: Bearer YOUR_API_KEY" \
          -H "Content-Type: application/json" \
          -d '{
            "model": "nano_banana_2",
            "prompt": "美丽的日出风景，金色的阳光洒在宁静的湖面上，远处是连绵的山脉",
            "aspect_ratio": "16:9"
          }'
        ```


        **请求体（JSON）：**

        ```json

        {
          "model": "nano_banana_2",
          "prompt": "美丽的日出风景，金色的阳光洒在宁静的湖面上，远处是连绵的山脉",
          "aspect_ratio": "16:9"
        }

        ```


        ### 图生图模式（URL 格式）

        ```bash

        curl -X POST https://xxxxx.com/v1/videos \
          -H "Authorization: Bearer YOUR_API_KEY" \
          -H "Content-Type: application/json" \
          -d '{
            "model": "nano_banana_2",
            "prompt": "将这张图片转换成油画风格",
            "aspect_ratio": "16:9",
            "images": [
              "https://example.com/images/reference1.jpg",
              "https://example.com/images/reference2.png"
            ]
          }'
        ```


        **请求体（JSON）：**

        ```json

        {
          "model": "nano_banana_2",
          "prompt": "美丽的日出风景，金色的阳光洒在宁静的湖面上，远处是连绵的山脉",
          "aspect_ratio": "16:9",
          "images": [
            "https://xxxxxxxx.jpg",
            "https://xxxxxxxx.png"
          ]
        }

        ```


        ### 图生图模式（Base64 格式）

        ```bash

        curl -X POST https://xxxxx.com/v1/videos \
          -H "Authorization: Bearer YOUR_API_KEY" \
          -H "Content-Type: application/json" \
          -d '{
            "model": "nano_banana_2",
            "prompt": "将这张图片转换成油画风格",
            "aspect_ratio": "16:9",
            "images": [
              "data:image/jpeg;base64,/9j/4AAQSkZJRg...",
              "data:image/png;base64,iVBORw0KGgoAAAANSU..."
            ]
          }'
        ```


        ## 响应参数


        | 参数名 | 类型 | 说明 |

        |--------|------|------|

        | id | string | 任务 ID，格式：`task_nano_xxx` 或 `task_xxx` |

        | object | string | 对象类型，固定值：`image` |

        | model | string | 使用的模型名称 |

        | status | string |
        任务状态：`queued`（排队中）、`processing`（处理中）、`completed`（已完成）、`failed`（失败） |

        | progress | number | 任务进度，0–100 |

        | created | number | 创建时间戳（秒），提交成功时返回 |

        | created_at | number | 创建时间戳（秒），任务失败时返回 |

        | completed_at | number | 完成时间戳（秒），仅在 `failed` 或 `completed` 状态返回 |

        | url | string | 生成的图片 URL（仅在 `completed` 状态返回） |

        | error | object | 错误信息（仅在 `failed` 状态返回） |

        | error.message | string | 失败原因描述 |

        | error.code | string | 错误码，如 `upstream_error` |


        ## 响应示例


        ### 提交成功（排队中）

        ```json

        {
          "id": "task_xxxxxxxxxxxxx",
          "object": "image",
          "model": "nano_banana_2",
          "status": "queued",
          "progress": 0,
          "created": 1709876543
        }

        ```


        ### 任务完成

        ```json

        {
          "id": "task_xxxxxxxxxxxxx",
          "object": "image",
          "model": "nano_banana_2",
          "status": "completed",
          "progress": 100,
          "created": 1709876543,
          "url": "https://example.com/images/xxx.jpg"
        }

        ```


        ### 任务失败

        ```json

        {
          "id": "task_xxxx",
          "object": "image",
          "model": "nano_banana_2",
          "status": "failed",
          "created_at": 1718123456,
          "completed_at": 1718123456,
          "progress": 100,
          "error": {
            "message": "上游任务失败原因",
            "code": "upstream_error"
          }
        }

        ```


        ## 注意事项


        1. **接口复用**：图片生成使用 `/v1/videos` 接口，与视频生成共用；通过 `model` 参数区分（`nano_banana`
        开头为图片生成）。

        2. **参数位置**：`aspect_ratio`、`images` 为顶层字段，直接放在请求体根对象中。

        3. **参考图片格式**：支持 JPEG、PNG、WEBP，单张图片最大 10MB。

        4. **参考图片数量**：最多 5 张。

        5. **参考图片来源**：
           - **Base64**：需包含完整的 Data URL 前缀（如 `data:image/jpeg;base64,`）
           - **URL**：直接传入可公网访问的图片地址
        6. **任务模式**：
           - 不传 `images` 或传空数组 = 文生图
           - `images` 含图片（URL 或 Base64）= 图生图
        7. **异步处理**：接口返回任务 ID 后，需通过轮询查询任务进度和结果。

        8. **分辨率档位**：Pro 版分辨率由 `model` 名称后缀决定（如 `nano_banana_pro-2K`），无需额外传尺寸参数。
      tags:
        - 图片生成（Images）
      parameters:
        - name: Authorization
          in: header
          description: 令牌
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
                  description: |-
                    模型名称
                    nano_banana_2、nano_banana_pro
                prompt:
                  type: string
                  description: 提示词
                aspect_ratio:
                  type: string
                images:
                  type: array
                  items:
                    type: string
              required:
                - model
                - prompt
                - aspect_ratio
                - images
              x-apifox-orders:
                - model
                - prompt
                - aspect_ratio
                - images
            example:
              model: nano_banana_2
              prompt: 美丽的日出风景，金色的阳光洒在宁静的湖面上，远处是连绵的山脉
              aspect_ratio: '16:9'
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
                  created:
                    type: integer
                  url:
                    type: string
                required:
                  - id
                  - object
                  - model
                  - status
                  - progress
                  - created
                  - url
                x-apifox-orders:
                  - id
                  - object
                  - model
                  - status
                  - progress
                  - created
                  - url
              example:
                id: task_xxxxxxxxxxxxx
                object: image
                model: nano_banana_2
                status: completed
                progress: 100
                created: 1709876543
                url: https://example.com/images/xxx.jpg
          headers: {}
          x-apifox-name: 成功
      security: []
      x-apifox-folder: 图片生成（Images）
      x-apifox-status: developing
      x-run-in-apifox: https://app.apifox.com/web/project/7902379/apis/api-424561006-run
components:
  schemas: {}
  securitySchemes: {}
servers: []
security: []

```
