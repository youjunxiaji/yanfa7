# TMB 账号

## 业务背景

网页版（tmb_web_v1）的载荷简化把每个项目的配置存在 TMB 服务器的数据库里。应用登录 TMB 账号后，
载荷简化页的「保存配置」把现在的配置存成网页版的一条记录，「历史记录」按项目名查这些配置、点一条回填到参数栏；
网页版和这边存的是同一种记录，两边都查得到。网页版存记录的规则不改，这边照着用。
登录不是必需的：连不上内网时工具照常用，只有查、存历史记录要登录。

## 数据流

```text
渲染层 stores/account.ts ──HTTP──> 本地后端 app_account / app_simpleLoad ──httpx──> http://10.0.3.198/v1/api
                                       └─ common/tmb_web.py（转发、报错翻译）
```

- 登录 `POST /api/account/login` → tmb_web_v1 `/users/login/`；续期 `POST /api/account/refresh` → `/users/refresh/`；
  当前登录的人 `GET /api/account/me` → `/users/user/`；查历史记录 `GET /api/simple-load/histories?query=`、
  保存配置 `POST /api/simple-load/histories` → `/shanghai_yanfa7/simple-load-calculation-histories/`（查和存同一个地址）。
- 令牌存在渲染层，经兼容垫片持久化到 `account.json`（不存密码）；要登录的接口带 `Authorization: Bearer` 给本地后端，
  后端只转发、不留存。

## 业务约定

- 服务器地址开发、打包都固定连生产 `10.0.3.198`，历史记录在生产库里。
- 登录成功时 tmb_web_v1 会经 WebSocket 通知同一账号的网页版下线（`LoginView` 的单点登录），登录框里写明了。
  所以尽量少让人重新登录：启动时调一次 `me`，顺带续期。
- JWT：access 15 分钟、refresh 7 天，tmb_web_v1 开了 `ROTATE_REFRESH_TOKENS`，续期时 refresh 也换新、重新计 7 天；
  没开黑名单，退出登录只丢本机的令牌。渲染层按 JWT 的 `exp` 提前 30 秒续期，几个请求同时过期共用一次续期；
  接口回 401 时强制续期重试一次，续期也回 401 就退出登录。连不上服务器时留着登录状态。
- 后端报错：令牌无效 401；连不上、超时、服务器 5xx 是 502；其余 400，`detail` 取 tmb_web_v1 的原话（如「账号或密码不正确」）：
  先取 `detail`，再取 `message`（存历史记录失败时网页版回 `{"status": "error", "message": ...}`），再取第一个字段错误。
- 客户端 `trust_env=False`：不走系统和环境变量的代理，开发机 `all_proxy` 是 socks 时 httpx 建客户端就会报缺 socksio。
- 查历史记录：tmb_web_v1 只返回自己存的、项目名模糊匹配、最多 10 条、不排序，后端按 `id` 倒序，新建的在前。网页版字段到这边的对应见
  `app_simpleLoad/serializers.py` 的 `HistoryRecord.from_tmb`：标题行行号 `title_row` 换成跳过行数（+1，None 是 0），
  「占位符」列是不用的列，区间表的格子数字、数字字符串、空串都有，缺的字段按网页版默认值补。
- 存历史记录（tmb_web_v1 `SimpleLoadCalculationHistoryView.post`）：按「登录的人 + 项目名」`update_or_create`，
  项目名是输出目录（`result_folder_save_path`）的最后一段。没存过就新建；存过同名的，五块 JSON 整条换成这次的，
  id 不变。响应只有「保存成功」，分不出新建还是覆盖。项目名一字不差才算同名（PostgreSQL 区分大小写），不同的人各存各的。
  表里没有时间字段，按 `id` 排的是第一次存的先后；也没有唯一约束，并发建出两条同名的以后，再存这个项目会报「保存失败」。
  存要有 `add_simpleloadcalculationhistorymodel` 权限（`DjangoModelPermissions`），没有时回 403，原话照转。
- 存的报文由 `HistorySaveRequest.to_tmb` 换成网页版「存储」发的写法，网页版照样能回填：不用的列叫「占位符1」「占位符2」……，
  跳过行数换回标题行行号（不跳是 None），区间表只存参与分组的分量、按 Fx 到 Mz 排、空格子写空串。
  输出目录先去掉首尾空白和末尾的斜杠，否则网页版取出的项目名是空串；去掉后还是空的不转发，回 400。
- 回填用记录里的跳过行数和列对应，不按文件重新认；列数按第一个 txt 补齐或截断。载荷文件夹在本机不存在时，
  文件格式区显示读不到，跳过行数和列对应仍是记录里的，这时保存不会存成回填前的；改路径后按文件重新认。

## 接口与页面

- 侧栏底部的账号入口（`SideNav.vue`）：没登录点开登录弹窗（`LoginModal.vue`，挂在 `App.vue`，哪里要登录就把
  `account.loginVisible` 设成 true）；登录后点开显示工号、部门和「退出登录」。
- 载荷简化标题栏右侧「保存配置」（`SimpleLoadView.vue`）：没选输出目录先提示，没登录先打开登录弹窗、登录完接着弹确认；
  确认框写明要存成的项目名和同名会被覆盖，确认后把 `simpleLoad` store 的 `historyConfig` 发给后端。
- 「历史记录」打开 `SimpleLoadHistory.vue`：没登录显示登录入口，登录后边打边查，点一行调
  `simpleLoad` store 的 `applyHistory`。
- 测试：`app_account/tests/test_views.py`、`app_simpleLoad/tests/test_history.py`（查和存，含存了再查回来一致），
  假 TMB 服务器 `tmb_server` 在 `backend/conftest.py`。

## 关键文件路径

```text
backend/common/tmb_web.py                              # 服务器地址、转发、报错翻译
backend/app_account/                                   # 登录、续期、当前登录的人
backend/app_simpleLoad/views.py                        # histories、save_history
backend/app_simpleLoad/serializers.py                  # HistoryRecord.from_tmb、HistorySaveRequest.to_tmb：两种写法互换
frontend/src/renderer/src/api/account.ts               # requestJson（401 抛 AuthExpiredError）
frontend/src/renderer/src/stores/account.ts            # 登录状态、续期、withAccess
frontend/src/renderer/src/components/LoginModal.vue
frontend/src/renderer/src/components/SimpleLoadHistory.vue
frontend/src/renderer/src/views/SimpleLoadView.vue     # 「保存配置」按钮和确认框
frontend/src/renderer/src/shims/tauri-bridge.ts        # account.load / save → account.json
```
