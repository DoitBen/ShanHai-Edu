# image2（流式）

## OpenAPI Specification

```yaml
openapi: 3.0.1
info:
  title: ''
  description: ''
  version: 1.0.0
paths:
  /v1/images/generations:
    post:
      summary: image2（流式）
      deprecated: false
      description: >
        # gpt-image-2 接口文档（/v1/images/generations OpenAI 原生格式）


        ## 接口地址

        - 文生图：`POST /v1/images/generations`

        - 图生图（图片编辑）：`POST /v1/images/edits`


        ## 功能说明

        采用 OpenAI 兼容格式的图片生成接口，支持文生图和图生图两种模式，支持同步返回和异步任务两种调用方式。



        ## 支持的模型


        | model 参数 | 说明 |

        |-----------|------|

        | `image2` | GPT 图片生成模型 |


        ## 请求头


        | 参数名 | 类型 | 必填 | 说明 |

        |--------|------|------|------|

        | Authorization | string | 是 | Bearer YOUR_API_KEY |

        | Content-Type | string | 是 | 文生图 / 图生图均支持 **`application/json`** 与
        **`multipart/form-data`** |


        ---


        ## 一、文生图接口


        ### 接口地址

        `POST /v1/images/generations`


        ### 请求参数


        | 参数名 | 类型 | 必填 | 说明 |

        |--------|------|------|------|

        | model | string | 是 | 模型名称，固定为 `image2` |

        | prompt | string | 是 | 图片描述，用于生成图片 |

        | size | string | 否 | 图片尺寸，格式自己定义 |

        | image | string 或 string[] | 否 | **带参考图**：单张传字符串，多张传数组。不传则为纯文生图 |


        ### 请求示例（JSON 格式 — 纯文生图）

        ```bash

        curl -X POST "https://xxxxxx.com/v1/images/generations" \
          -H "Authorization: Bearer YOUR_API_KEY" \
          -H "Content-Type: application/json" \
          -d '{
            "model": "image2",
            "prompt": "生成竖屏图片 xxx抖音带货",
            "size": "1024x1792"
          }'
        ```


        ### 请求示例（JSON 格式 — 带参考图 URL，单图或多图）

        ```bash

        curl -X POST "https://xxxxxx.com/v1/images/generations" \
          -H "Authorization: Bearer YOUR_API_KEY" \
          -H "Content-Type: application/json" \
          -d "{
            \"model\": \"image2\",
            \"prompt\": \"广告\",
            \"size\": \"1024x1792\",
            \"image\": [
              \"https://res.papir.cc/user-upload/creati-web-app/2026-04-18/1776519962551vv1AXmBu-ZMWqAckJIbt81167-600x751h.jpg\",
              \"https://www.baidu.com/img/PCtm_d9c8750bed0b3c7d089fa7d55720d6cf.png\"
            ]
          }"
        ```



        ### 请求示例（表单格式）

        ```bash

        curl -X POST "https://xxxxxx.com/v1/images/generations" \
          -H "Authorization: Bearer YOUR_API_KEY" \
          -H "Content-Type: multipart/form-data" \
          --form 'prompt="生成竖屏图片 xxx抖音带货"' \
          --form 'model="image2"' \
          --form 'size="1024x1792"'
        ```


        ---


        ## 二、图生图（图片编辑）接口


        ### 接口地址

        `POST /v1/images/edits`



        ### 请求参数


        | 参数名 | 类型 | 必填 | 说明 |

        |--------|------|------|------|

        | model | string | 是 | 模型名称，固定为 `image2` |

        | prompt | string | 是 | 图片描述，用于编辑图片 |

        | image | 见说明 | 是 | **JSON**：`string`（单图）或
        `string[]`（多图），**Multipart**：一个或多个 **文件** 字段（字段名依上游约定，常见为 `image` /
        `image[]`） |

        | size | string | 否 | 图片尺寸，格式同文生图 |


        ### 请求示例（JSON — URL 或多图 URL）


        ```bash

        curl -X POST "https://xxxxxx.com/v1/images/edits" \
          -H "Authorization: Bearer YOUR_API_KEY" \
          -H "Content-Type: application/json" \
          -d '{
            "model": "image2",
            "prompt": "变成灰色",
            "size": "1024x1792",
            "image": "https://example.com/reference.png"
          }'
        ```


        ### 请求示例（JSON — Data URL / Base64）


        ```json

        {
          "model": "image2",
          "prompt": "变成灰色",
          "size": "1024x1792",
          "image": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
        }

        ```


        多图时 `"image": ["data:image/png;base64,...", "https://..."]` 与
        `generations` 用法一致。


        ### 请求示例（表单格式 - 本地文件）

        ```bash

        curl -X POST "https://xxxxxx.com/v1/images/edits" \
          -H "Authorization: Bearer YOUR_API_KEY" \
          --form 'image=@"/path/to/example.jpg"' \
          --form 'prompt="变成灰色"' \
          --form 'model="image2"' \
          --form 'size="1024x1792"'
        ```


        ### 请求示例（多图上传）

        ```bash

        curl -X POST "https://xxxxxx.com/v1/images/edits" \
          -H "Authorization: Bearer YOUR_API_KEY" \
          --form 'image[]=@"/path/to/example1.jpg"' \
          --form 'image[]=@"/path/to/example2.jpg"' \
          --form 'prompt="变成灰色"' \
          --form 'model="image2"' \
          --form 'size="1024x1792"'
        ```


        ### Python 示例（JSON，直接传 URL）


        ```python

        import httpx


        resp = httpx.post(
            "https://xxxxxx.com/v1/images/edits",
            headers={"Authorization": "Bearer YOUR_API_KEY"},
            json={
                "model": "image2",
                "prompt": "变成灰色",
                "size": "1024x1792",
                "image": "https://example.com/reference.png",
            },
        )

        print(resp.json())

        ```


        ### Python 示例（multipart 上传本地文件）


        ```python

        import httpx


        img_bytes = httpx.get("https://example.com/reference.png").content


        resp = httpx.post(
            "https://xxxxxx.com/v1/images/edits",
            headers={"Authorization": "Bearer YOUR_API_KEY"},
            files={"image": ("image.png", img_bytes, "image/png")},
            data={"model": "image2", "prompt": "变成灰色", "size": "1024x1792"},
        )

        print(resp.json())

        ```


        ---


        ## 三、响应示例


        ### 同步响应 - Base64 格式（默认）

        ```json

        {
          "created": 1234567890,
          "data": [
            {
              "b64_json": "data:image/png;base64,iVBORw0KGgoAAAANSU..."
            }
          ]
        }

        ```



        ### 任务状态说明


        | status | 说明 |

        |--------|------|

        | `queued` | 任务排队中 |

        | `in_progress` | 任务处理中 |

        | `completed` | 任务已完成 |

        | `failed` | 任务失败 |


        ---



        ## 注意事项


        1. **接口格式**：采用 OpenAI 兼容的原生图片接口格式，与 OpenAI 官方 SDK 通用

        2. **调用方式**：接口直接返回生成结果，适合对实时性要求高的场景

        3. **响应格式**：
           - `b64_json`（默认）：直接返回 Base64 编码的图片数据，前端可直接渲染
        4. **尺寸支持**：
           - 竖屏：`1024x1792`
           - 横屏：`1792x1024`
           - 方形：`1024x1024`
           - 其他尺寸：可在size参数自由设置
        5. **参考图与格式**：`/v1/images/generations` 与 **`/v1/images/edits`** 均可在
        **`application/json`** 下用 **`image`** 传 **URL** 或 **Base64 / Data
        URL**（字符串或数组）；需要走文件流时用 **`multipart/form-data`**。具体字段名、是否支持裸 Base64
        以实际上游实现为准

        6. **参考图片格式**：支持 JPEG、PNG、WEBP 格式，最多10张图片

        7. **图片有效期**：返回的图片 URL 有效期为 2 小时，请及时下载保存

        8. **模型区别**：该接口使用模型名 `image2`，如需通过 `/v1/videos` 接口调用，请使用模型名
        `gpt-image-2`
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
                size:
                  type: string
                image:
                  type: array
                  items:
                    type: string
              required:
                - model
                - prompt
                - size
                - image
              x-apifox-orders:
                - model
                - prompt
                - size
                - image
            example:
              model: image2
              prompt: 根据图片做一个广告
              size: 1024x1792
              image:
                - https://xxxxxxxx.jpg
                - https://xxxxxxxx.png
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
      x-run-in-apifox: https://app.apifox.com/web/project/7902379/apis/api-447357296-run
components:
  schemas: {}
  securitySchemes: {}
servers: []
security: []

```
