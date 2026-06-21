# 任务查询

## OpenAPI Specification

```yaml
openapi: 3.0.1
info:
  title: ''
  description: ''
  version: 1.0.0
paths:
  /v1/videos/{task_id}:
    get:
      summary: 任务查询
      deprecated: false
      description: >
        # 任务查询接口文档


        ## 接口地址

        `GET /v1/videos/{task_id}`


        ## 功能说明

        查询视频生成和图片生成任务的状态和结果（适用于Sora、Veo、图片生成等所有任务）


        ## 请求头


        | 参数名 | 类型 | 必填 | 说明 |

        |--------|------|------|------|

        | Authorization | string | 是 | Bearer YOUR_API_KEY |


        ## 路径参数


        | 参数名 | 类型 | 必填 | 说明 |

        |--------|------|------|------|

        | task_id | string | 是 | 任务ID，由提交接口返回 |


        ## 请求示例


        ```bash

        curl -X GET https://xxx.com/v1/videos/task_xxxxxxxxxxxxx \
          -H "Authorization: Bearer YOUR_API_KEY"
        ```


        ## 响应参数


        | 参数名 | 类型 | 说明 |

        |--------|------|------|

        | id | string | 任务ID |

        | object | string | 对象类型：video（视频）或 image（图片） |

        | model | string | 使用的模型名称 |

        | status | string |
        任务状态：queued（排队中）、processing（处理中）、completed（已完成）、failed（失败） |

        | progress | number | 任务进度，0-100 |

        | created_at | number | 创建时间戳（秒） |

        | completed_at | number | 完成时间戳（秒，仅completed状态返回） |

        | url | string | 结果URL（仅completed状态返回），视频或图片的下载地址 |

        | error | string | 错误信息（仅failed状态返回） |


        ## 响应示例


        ### 排队中

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


        ### 处理中

        ```json

        {
          "id": "task_xxxxxxxxxxxxx",
          "object": "video",
          "model": "veo_3_1-fast",
          "status": "processing",
          "progress": 45,
          "created_at": 1709876543
        }

        ```


        ### 已完成（视频）

        ```json

        {
          "id": "task_xxxxxxxxxxxxx",
          "object": "video",
          "model": "sora-2-landscape-10s",
          "status": "completed",
          "progress": 100,
          "created_at": 1709876543,
          "completed_at": 1709876600,
          "url": "https://example.com/videos/xxx.mp4"
        }

        ```


        ### 已完成（图片 - Nano Banana）

        ```json

        {
          "id": "task_xxxxxxxxxxxxx",
          "object": "image",
          "model": "nano_banana_2",
          "status": "completed",
          "progress": 100,
          "created_at": 1709876543,
          "completed_at": 1709876580,
          "url": "https://example.com/images/xxx.jpg"
        }

        ```


        ### 失败

        ```json

        {
          "id": "task_xxxxxxxxxxxxx",
          "object": "video",
          "model": "sora-2-landscape-10s",
          "status": "failed",
          "progress": 0,
          "created_at": 1709876543,
          "error": "生成失败：内容违规"
        }

        ```


        ## 错误码说明


        | HTTP状态码 | 说明 |

        |-----------|------|

        | 200 | 请求成功 |

        | 404 | 任务不存在 |

        | 401 | 未授权 |

        | 500 | 服务器内部错误 |


        ## 注意事项


        1. **轮询建议**：建议每3-5秒轮询一次任务状态，避免过于频繁的请求

        2. **任务状态流转**：queued → processing → completed/failed

        3. **结果获取**：只有当 `status` 为 `completed` 时，才会返回 `url` 字段

        4. **通用接口**：此接口适用于所有通过 `/v1/videos` 提交的任务（Sora视频、Veo视频、Nano Banana图片生成等）

        5. **任务保留**：已完成的任务会保留一段时间，建议及时下载结果
      tags:
        - 视频生成（Videos）
      parameters:
        - name: task_id
          in: path
          description: ''
          required: true
          schema:
            type: string
        - name: Authorization
          in: header
          description: ''
          required: true
          example: Bearer {{YOUR_API_KEY}}
          schema:
            type: string
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
                  url:
                    type: string
                required:
                  - id
                  - object
                  - model
                  - status
                  - progress
                  - created_at
                  - completed_at
                  - url
                x-apifox-orders:
                  - id
                  - object
                  - model
                  - status
                  - progress
                  - created_at
                  - completed_at
                  - url
              example:
                id: task_xxxxxxxxxxxxx
                object: video
                model: sora-2-landscape-10s
                status: completed
                progress: 100
                created_at: 1709876543
                completed_at: 1709876600
                url: https://example.com/videos/xxxxxxxxxxxxxxxxxxxxx
          headers: {}
          x-apifox-name: 成功
      security: []
      x-apifox-folder: 视频生成（Videos）
      x-apifox-status: developing
      x-run-in-apifox: https://app.apifox.com/web/project/7902379/apis/api-424659184-run
components:
  schemas: {}
  securitySchemes: {}
servers: []
security: []

```
