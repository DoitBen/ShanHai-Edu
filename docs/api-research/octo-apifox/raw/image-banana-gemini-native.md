# 香蕉（gemini原生格式） 

## OpenAPI Specification

```yaml
openapi: 3.0.1
info:
  title: ''
  description: ''
  version: 1.0.0
paths:
  /v1beta/models/{model}:generateContent:
    post:
      summary: '香蕉（gemini原生格式） '
      deprecated: false
      description: >
        # 图片生成接口文档


        ## 接口地址


        ```

        POST /v1beta/models/{model}:generateContent

        ```


        ## 功能说明


        支持**文生图**和**图生图**两种模式，同步返回。


        ---


        ## 支持的模型


        | model | 说明 |

        |-------|------|

        | `gemini-3-pro-image-preview` | 专业版，画质强、一致性高 |

        | `gemini-3.1-flash-image-preview` | 快速版，响应更快，支持更多宽高比和分辨率选项 |


        模型名填写在 URL 路径中，例如：


        ```

        POST /v1beta/models/gemini-3.1-flash-image-preview:generateContent

        ```


        ---


        ## 请求头


        | 参数名 | 必填 | 说明 |

        |--------|------|------|

        | `Authorization` | 是 | `Bearer YOUR_API_KEY` |

        | `Content-Type` | 是 | `application/json` |


        ---


        ## 请求参数


        | 参数名 | 类型 | 必填 | 说明 |

        |--------|------|------|------|

        | `contents` | array | 是 | 对话内容列表 |

        | `contents[].role` | string | 是 | 固定填 `"user"` |

        | `contents[].parts` | array | 是 | 内容部件数组 |

        | `contents[].parts[].text` | string | 是 | 图片描述提示词 |

        | `contents[].parts[].inlineData` | object | 否 | 参考图片（Base64 方式），图生图时二选一
        |

        | `contents[].parts[].inlineData.mimeType` | string | 是 | 图片格式，如
        `image/jpeg`、`image/png`、`image/webp` |

        | `contents[].parts[].inlineData.data` | string | 是 | 图片的纯 Base64
        字符串（**不含** `data:image/jpeg;base64,` 前缀） |

        | `contents[].parts[].fileData` | object | 否 | 参考图片（URL 方式），图生图时二选一 |

        | `contents[].parts[].fileData.mimeType` | string | 否 | 图片格式，如
        `image/jpeg`、`image/png`、`image/webp`，可省略 |

        | `contents[].parts[].fileData.fileUri` | string | 是 | 图片的 HTTP/HTTPS
        直链地址 |

        | `generationConfig` | object | 否 | 生成配置 |

        | `generationConfig.responseModalities` | array | 否 | 返回内容模态，固定传
        `["IMAGE"]` |

        | `generationConfig.imageConfig` | object | 否 | 图片生成配置 |

        | `generationConfig.imageConfig.aspectRatio` | string | 否 |
        输出图片宽高比，见下方支持列表 |

        | `generationConfig.imageConfig.imageSize` | string | 否 | 输出分辨率：`1K` /
        `2K` / `4K`，仅 `gemini-3.1-flash-image-preview` 支持 |


        ### 支持的宽高比（aspectRatio）


        两个模型均支持：


        ```

        1:1  2:3  3:2  3:4  4:3  4:5  5:4  9:16  16:9  21:9

        ```


        仅 `gemini-3.1-flash-image-preview` 额外支持：


        ```

        1:4  4:1  1:8  8:1

        ```


        ---


        ## 请求示例


        ### 文生图


        ```bash

        curl -X POST
        https://xxx.com/v1beta/models/gemini-3.1-flash-image-preview:generateContent
        \
          -H "Authorization: Bearer YOUR_API_KEY" \
          -H "Content-Type: application/json" \
          -d '{
            "contents": [
              {
                "role": "user",
                "parts": [
                  {
                    "text": "A futuristic city skyline at sunset, cinematic lighting, 4K"
                  }
                ]
              }
            ],
            "generationConfig": {
              "responseModalities": ["IMAGE"],
              "imageConfig": {
                "aspectRatio": "16:9",
                "imageSize": "2K"
              }
            }
          }'
        ```


        ### 图生图（单张参考图，Base64 方式）


        ```json

        {
          "contents": [
            {
              "role": "user",
              "parts": [
                {
                  "inlineData": {
                    "mimeType": "image/jpeg",
                    "data": "/9j/4AAQSkZJRg..."
                  }
                },
                {
                  "text": "Change the background to a peaceful sunny beach, keep the main subject unchanged"
                }
              ]
            }
          ],
          "generationConfig": {
            "responseModalities": ["IMAGE"],
            "imageConfig": {
              "aspectRatio": "1:1"
            }
          }
        }

        ```


        ### 图生图（单张参考图，URL 方式）


        ```json

        {
          "contents": [
            {
              "role": "user",
              "parts": [
                {
                  "fileData": {
                    "mimeType": "image/jpeg",
                    "fileUri": "https://example.com/your-image.jpg"
                  }
                },
                {
                  "text": "Change the background to a peaceful sunny beach, keep the main subject unchanged"
                }
              ]
            }
          ],
          "generationConfig": {
            "responseModalities": ["IMAGE"],
            "imageConfig": {
              "aspectRatio": "1:1"
            }
          }
        }

        ```


        ### 图生图（多张参考图）


        ```json

        {
          "contents": [
            {
              "role": "user",
              "parts": [
                {
                  "inlineData": {
                    "mimeType": "image/jpeg",
                    "data": "/9j/4AAQSkZJRg..."
                  }
                },
                {
                  "inlineData": {
                    "mimeType": "image/png",
                    "data": "iVBORw0KGgoAAAANSU..."
                  }
                },
                {
                  "text": "Blend the style of both images and generate a new landscape"
                }
              ]
            }
          ],
          "generationConfig": {
            "responseModalities": ["IMAGE"]
          }
        }

        ```


        ---


        ## 响应参数


        | 参数名 | 类型 | 说明 |

        |--------|------|------|

        | `created` | number | 生成时间戳（Unix 秒） |

        | `model` | string | 使用的模型名 |

        | `candidates` | array | 结果列表 |

        | `candidates[].content.parts[].image_url.url` | string | 生成的图片 URL |

        | `candidates[].finishReason` | string | 完成原因，正常为 `"STOP"` |

        | `data` | array | 原始数据，`data[0].url` 可直接取图片地址 |


        ---


        ## 响应示例


        ```json

        {
          "created": 1780125491,
          "model": "gemini-3.1-flash-image-preview",
          "candidates": [
            {
              "content": {
                "parts": [
                  {
                    "image_url": {
                      "url": "https://cdn.example.com/output/xxx.png"
                    }
                  }
                ]
              },
              "finishReason": "STOP"
            }
          ],
          "data": [
            {
              "url": "https://cdn.example.com/output/xxx.png"
            }
          ]
        }

        ```


        ---


        ## 提取图片地址


        图片 URL 有两个等价的取法：


        ```javascript

        // 方式一：通过 candidates

        const url = response.candidates[0].content.parts[0].image_url.url;


        // 方式二：通过 data（更简洁）

        const url = response.data[0].url;

        ```


        ---


        ## 注意事项


        1. **同步接口**：图片生成完毕后一次性返回，建议客户端超时时间设置为 **120 秒**以上

        2. **text 为必填**：无论文生图还是图生图，`parts` 中必须包含 `text` 字段

        3. **参考图片格式**：支持 `image/jpeg`、`image/png`、`image/webp`，单张建议不超过 **5MB**

        4. **传图两种方式**：`inlineData`（Base64）和 `fileData`（URL
        直链）均可，同一请求中可混用；`fileData` 使用 `fileUri` 字段传入图片 HTTP/HTTPS 地址

        5. **参考图片数量**：最多 **14** 张

        6. **imageSize 字段**：仅 `gemini-3.1-flash-image-preview`
        支持，`gemini-3-pro-image-preview` 请勿传此参数

        7. **图片 URL 有效期**：返回的图片链接请及时下载或转存，不建议长期依赖直链
      tags:
        - 图片生成（Images）
      parameters:
        - name: model
          in: path
          description: ''
          required: true
          schema:
            type: string
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
                contents:
                  type: array
                  items:
                    type: object
                    properties:
                      role:
                        type: string
                      parts:
                        type: array
                        items:
                          type: object
                          properties:
                            fileData:
                              type: object
                              properties:
                                mimeType:
                                  type: string
                                fileUri:
                                  type: string
                              required:
                                - mimeType
                                - fileUri
                              x-apifox-orders:
                                - mimeType
                                - fileUri
                            text:
                              type: string
                          x-apifox-orders:
                            - fileData
                            - text
                          required:
                            - text
                    x-apifox-orders:
                      - role
                      - parts
                    required:
                      - role
                generationConfig:
                  type: object
                  properties:
                    responseModalities:
                      type: array
                      items:
                        type: string
                    imageConfig:
                      type: object
                      properties:
                        aspectRatio:
                          type: string
                      x-apifox-orders:
                        - aspectRatio
                  x-apifox-orders:
                    - responseModalities
                    - imageConfig
              required:
                - contents
              x-apifox-orders:
                - contents
                - generationConfig
            example:
              contents:
                - role: user
                  parts:
                    - fileData:
                        mimeType: image/jpeg
                        fileUri: >-
                          https://www.baidu.com/img/PCtm_d9c8750bed0b3c7d089fa7d55720d6cf.png
                    - text: 做个广告
              generationConfig:
                responseModalities:
                  - IMAGE
                imageConfig:
                  aspectRatio: '21:9'
      responses:
        '200':
          description: ''
          content:
            application/json:
              schema:
                type: object
                properties:
                  created:
                    type: integer
                  model:
                    type: string
                  candidates:
                    type: array
                    items:
                      type: object
                      properties:
                        content:
                          type: object
                          properties:
                            parts:
                              type: array
                              items:
                                type: object
                                properties:
                                  image_url:
                                    type: object
                                    properties:
                                      url:
                                        type: string
                                    required:
                                      - url
                                    x-apifox-orders:
                                      - url
                                x-apifox-orders:
                                  - image_url
                          required:
                            - parts
                          x-apifox-orders:
                            - parts
                        finishReason:
                          type: string
                      x-apifox-orders:
                        - content
                        - finishReason
                  data:
                    type: array
                    items:
                      type: object
                      properties:
                        url:
                          type: string
                      x-apifox-orders:
                        - url
                required:
                  - created
                  - model
                  - candidates
                  - data
                x-apifox-orders:
                  - created
                  - model
                  - candidates
                  - data
              example:
                created: 1780125491
                model: gemini-3.1-flash-image-preview
                candidates:
                  - content:
                      parts:
                        - image_url:
                            url: https://cdn.example.com/output/xxx.png
                    finishReason: STOP
                data:
                  - url: https://cdn.example.com/output/xxx.png
          headers: {}
          x-apifox-name: 成功
      security: []
      x-apifox-folder: 图片生成（Images）
      x-apifox-status: developing
      x-run-in-apifox: https://app.apifox.com/web/project/7902379/apis/api-466136668-run
components:
  schemas: {}
  securitySchemes: {}
servers: []
security: []

```
