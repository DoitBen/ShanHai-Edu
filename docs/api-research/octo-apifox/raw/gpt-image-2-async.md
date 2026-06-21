# gpt-image-2（异步）

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
      summary: gpt-image-2（异步）
      deprecated: false
      description: >
        # gpt-image-2 接口文档（/v1/videos 视频接口格式）


        ## 接口地址

        `POST /v1/videos`


        ## 功能说明

        通过 `/v1/videos` 接口调用 GPT 图片生成能力（与视频生成共用接口，通过 `model`
        参数区分），支持文生图和图生图两种模式，采用异步任务方式，先提交返回任务 ID，再轮询获取结果。


        **画幅 / 宽高比**：通过顶层 `aspect_ratio` 参数传入比例字符串（如 `9:16`、`16:9`），支持 10 种比例。


        ## 支持的模型


        | model 参数 | 说明 |

        |-----------|------|

        | `gpt-image-2` | GPT 图片生成（标准档）。 |

        | `gpt-image-2-2K` | **2K** 分辨率。 |

        | `gpt-image-2-4K` | **4K** 分辨率。 |


        三者均走同一套 `/v1/videos` 异步流程，仅 `model` 不同；下游计费与上游路由以 `model` 区分档位。


        ## 请求头


        | 参数名 | 类型 | 必填 | 说明 |

        |--------|------|------|------|

        | Authorization | string | 是 | Bearer YOUR_API_KEY |

        | Content-Type | string | 是 | application/json |


        ## 请求参数


        | 参数名 | 类型 | 必填 | 说明 |

        |--------|------|------|------|

        | model | string | 是 | 模型名称，取值为
        `gpt-image-2`、`gpt-image-2-2K`、`gpt-image-2-4K` 之一（大小写须与上表一致，其中
        `2K`/`4K` 为大写 K） |

        | prompt | string | 是 | 文本提示词 |

        | aspect_ratio | string | 否 |
        宽高比，直接传比例字符串。支持：`1:1`、`5:4`、`9:16`、`21:9`、`16:9`、`3:2`、`4:3`、`4:5`、`3:4`、`2:3`，共
        10 种。不传默认 `1:1` |

        | images | string[] | 否 | 参考图片数组（支持 Base64 或 URL），最多 5
        张。传此参数为图生图模式，不传或传空数组为文生图模式 |


        ### `images` 数组元素传法


        | 方式 | 示例 |

        |------|------|

        | **图片 URL** | `"https://example.com/reference.jpg"` |

        | **Base64** | `"data:image/jpeg;base64,/9j/4AAQSkZJRg..."` |


        > **注意**：传入图片 URL 时，网关会自动将其下载并转为 Base64 后发给上游，请确保 URL 为**可公网访问的图片直链**。


        ## 请求示例


        ### 文生图模式（竖屏 9:16）

        ```bash

        curl -X POST https://xxxxxx.com/v1/videos \
          -H "Authorization: Bearer YOUR_API_KEY" \
          -H "Content-Type: application/json" \
          -d '{
            "model": "gpt-image-2",
            "prompt": "生成抖音带货风格主图，主体 xxx",
            "aspect_ratio": "9:16"
          }'
        ```


        **请求体（JSON）：**

        ```json

        {
          "model": "gpt-image-2",
          "prompt": "生成抖音带货风格主图，主体 xxx",
          "aspect_ratio": "9:16"
        }

        ```


        ### 文生图模式（横屏 16:9）

        ```bash

        curl -X POST https://xxxxxx.com/v1/videos \
          -H "Authorization: Bearer YOUR_API_KEY" \
          -H "Content-Type: application/json" \
          -d '{
            "model": "gpt-image-2",
            "prompt": "美丽的日出风景，金色的阳光洒在宁静的湖面上，远处是连绵的山脉",
            "aspect_ratio": "16:9"
          }'
        ```


        ### 文生图模式（2K / 4K 档位）


        将 `model` 改为 `gpt-image-2-2K` 或 `gpt-image-2-4K` 即可，`aspect_ratio`
        用法与标准档相同。


        ```bash

        curl -X POST https://xxxxxx.com/v1/videos \
          -H "Authorization: Bearer YOUR_API_KEY" \
          -H "Content-Type: application/json" \
          -d '{
            "model": "gpt-image-2-2K",
            "prompt": "生成抖音带货风格主图，主体 xxx",
            "aspect_ratio": "9:16"
          }'
        ```


        ### 图生图模式（Base64 格式）

        ```bash

        curl -X POST https://xxxxxx.com/v1/videos \
          -H "Authorization: Bearer YOUR_API_KEY" \
          -H "Content-Type: application/json" \
          -d '{
            "model": "gpt-image-2",
            "prompt": "将这张图片转换成油画风格",
            "aspect_ratio": "9:16",
            "images": [
              "data:image/jpeg;base64,/9j/4AAQSkZJRg...",
              "data:image/png;base64,iVBORw0KGgoAAAANSU..."
            ]
          }'
        ```


        ### 图生图模式（URL 格式）

        ```bash

        curl -X POST https://xxxxxx.com/v1/videos \
          -H "Authorization: Bearer YOUR_API_KEY" \
          -H "Content-Type: application/json" \
          -d '{
            "model": "gpt-image-2",
            "prompt": "将这张图片转换成油画风格",
            "aspect_ratio": "16:9",
            "images": [
              "https://example.com/images/reference1.jpg",
              "https://example.com/images/reference2.png"
            ]
          }'
        ```


        ## 响应参数


        | 参数名 | 类型 | 说明 |

        |--------|------|------|

        | id | string | 任务 ID，格式：`task_xxxx` |

        | object | string | 对象类型，固定值：`image` |

        | model | string | 使用的模型名称 |

        | status | string |
        任务状态：`queued`（排队中）、`in_progress`（处理中）、`completed`（已完成）、`failed`（失败） |

        | progress | number | 任务进度，0–100 |

        | created_at | number | 创建时间戳（秒） |

        | completed_at | number | 完成时间戳（秒），仅在 `completed` 或 `failed` 状态返回 |

        | url | string | 生成的图片 URL，仅在 `completed` 状态返回 |

        | error | object | 错误信息，仅在 `failed` 状态返回 |

        | error.message | string | 失败原因描述 |

        | error.code | string | 错误码，如 `upstream_error` |


        ## 响应示例


        ### 提交成功（排队中）

        ```json

        {
          "id": "task_1776831820897",
          "object": "image",
          "model": "gpt-image-2",
          "status": "queued",
          "progress": 0,
          "created_at": 1709876543
        }

        ```


        ### 任务处理中

        ```json

        {
          "id": "task_1776831820897",
          "object": "image",
          "model": "gpt-image-2",
          "status": "in_progress",
          "progress": 10,
          "created_at": 1709876543
        }

        ```


        ### 任务完成

        ```json

        {
          "id": "task_1776831820897",
          "object": "image",
          "model": "gpt-image-2",
          "status": "completed",
          "progress": 100,
          "created_at": 1709876543,
          "completed_at": 1709876598,
          "url": "https://example.com/uploads/gpt-images/task_1776831820897.png"
        }

        ```


        ### 任务失败

        ```json

        {
          "id": "task_1776831820897",
          "object": "image",
          "model": "gpt-image-2",
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


        ## 任务查询接口


        ### 接口地址

        `GET /v1/videos/{task_id}`


        ### 请求示例

        ```bash

        curl -X GET https://xxxxxx.com/v1/videos/task_1776831820897 \
          -H "Authorization: Bearer YOUR_API_KEY"
        ```


        ### 响应说明

        返回字段与提交接口一致，根据 `status` 字段判断任务是否完成：

        - `queued` / `in_progress`：任务未完成，继续轮询

        - `completed`：任务完成，从 `url` 字段获取图片地址

        - `failed`：任务失败，从 `error.message` 获取错误原因


        ## 注意事项


        1. **接口复用**：GPT 图片生成使用 `/v1/videos` 接口，与视频生成共用，通过 `model` 参数区分；GPT 图系列为
        `gpt-image-2`、`gpt-image-2-2K`、`gpt-image-2-4K`

        2. **参数位置**：`aspect_ratio`、`images` 为顶层字段，直接放在请求体根对象中

        3. **宽高比**：通过 `aspect_ratio` 传入比例字符串，支持以下 10 种值：

           | 值 | 方向 |
           |----|------|
           | `1:1` | 正方形 |
           | `5:4` | 横向 |
           | `9:16` | 竖向（短视频/手机） |
           | `21:9` | 超宽横向 |
           | `16:9` | 横向（宽屏） |
           | `3:2` | 横向 |
           | `4:3` | 横向 |
           | `4:5` | 竖向 |
           | `3:4` | 竖向 |
           | `2:3` | 竖向 |

           不传 `aspect_ratio` 时默认为 `1:1`。
        4. **参考图片格式**：支持 JPEG、PNG、WEBP 格式

        5. **参考图片来源**：支持两种格式
           - **Base64 格式**：需包含完整的 Data URL 前缀（如：`data:image/jpeg;base64,`）
           - **URL 格式**：直接传入可访问的图片 URL 地址
        6. **任务模式**：
           - 不传 `images` 或传空数组 = 文生图模式
           - `images` 包含图片（Base64 或 URL）= 图生图模式
        7. **异步处理**：接口返回任务 ID 后，需要通过轮询 `GET /v1/videos/{task_id}`
        查询任务进度和结果，建议轮询间隔 2~5 秒

        8. **图片有效期**：生成的图片地址有效期为 5 小时，请及时下载保存
      tags:
        - 图片生成（Images）
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
                prompt:
                  type: string
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
              model: gpt-image-2
              prompt: 根据图片做一个广告
              aspect_ratio: '16:9'
              images:
                - https://xxx.cc/xxx.jpg
                - >-
                  https://www.baidu.com/img/PCtm_d9c8750bed0b3c7d089fa7d55720d6cf.png
      responses:
        '200':
          description: ''
          content:
            application/json:
              schema:
                type: object
                properties: {}
          headers: {}
          x-apifox-name: 成功
      security: []
      x-apifox-folder: 图片生成（Images）
      x-apifox-status: developing
      x-run-in-apifox: https://app.apifox.com/web/project/7902379/apis/api-447634846-run
components:
  schemas: {}
  securitySchemes: {}
servers: []
security: []

```
