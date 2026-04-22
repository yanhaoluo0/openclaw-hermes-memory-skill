# 后端接口测试伪代码示例

本文档展示如何为后端工单编写验证脚本的思路。

---

## 用户认证模块测试

### 功能点 1: 注册

```python
describe('用户注册', () => {
  test('正常注册 → 返回用户信息 + Token', () => {
    # POST /api/auth/register
    # body: { username, phone, email, password }
    # 验证: 状态码 201, 返回 user_id, token
  });

  test('用户名已存在 → 400 错误', () => {
    # POST /api/auth/register
    # body: { username: 'existing' }
    # 验证: 状态码 400, error.message 包含 '用户名已存在'
  });

  test('手机号格式错误 → 422 验证错误', () => {
    # POST /api/auth/register
    # body: { phone: '12345' }
    # 验证: 状态码 422, 返回字段错误详情
  });

  test('密码太短 (< 8 位) → 422 验证错误', () => {
    # POST /api/auth/register
    # body: { password: '123' }
    # 验证: 状态码 422, 提示密码长度要求
  });

  test('缺少必填字段 → 422 验证错误', () => {
    # POST /api/auth/register
    # body: { username: 'test' }  # 缺少其他字段
    # 验证: 状态码 422, 列出缺失字段
  });
});
```

### 功能点 2: 登录

```python
describe('用户登录', () => {
  test('手机号+密码 登录成功', () => {
    # POST /api/auth/login
    # body: { phone, password }
    # 验证: 状态码 200, 返回 token, user_info
  });

  test('账号不存在 → 401 错误', () => {
    # POST /api/auth/login
    # body: { phone: '19900000000', password: 'xxx' }
    # 验证: 状态码 401, 提示账号不存在
  });

  test('密码错误 → 401 错误', () => {
    # POST /api/auth/login
    # body: { phone: '13800138000', password: 'wrong' }
    # 验证: 状态码 401, 提示密码错误
  });

  test('密码连续错误 5 次 → 账号锁定', () => {
    # 循环调用登录 (错误密码) 5 次
    # 验证: 第 5 次后返回 401, 提示账号已锁定
  });

  test('短信验证码登录 → 验证验证码', () => {
    # POST /api/auth/login/sms
    # body: { phone, code }
    # 验证: 状态码 200, 返回 token
  });

  test('短信验证码错误 → 401 错误', () => {
    # POST /api/auth/login/sms
    # body: { phone, code: '000000' }
    # 验证: 状态码 401, 提示验证码错误
  });

  test('短信验证码过期 → 401 错误', () => {
    # 等待验证码过期 (5分钟)
    # POST /api/auth/login/sms
    # 验证: 状态码 401, 提示验证码已过期
  });
});
```

### 功能点 3: Token 管理

```python
describe('Token 管理', () => {
  test('Token 有效期 2 小时', () => {
    # 登录获取 token
    # 验证 token 在 2 小时后过期
  });

  test('Refresh Token 续期', () => {
    # POST /api/auth/refresh
    # body: { refresh_token }
    # 验证: 返回新 access_token
  });

  test('Refresh Token 过期 → 需重新登录', () => {
    # 使用过期的 refresh_token
    # 验证: 状态码 401, 提示需重新登录
  });

  test('登出 → Token 失效', () => {
    # POST /api/auth/logout
    # Header: Authorization: Bearer {token}
    # 验证: 状态码 200
    # 验证: 再次用该 token 请求 → 401
  });
});
```

---

## 用户管理模块测试

### 功能点 1: 权限控制

```python
describe('权限控制', () => {
  test('普通用户 → 禁止访问管理接口', () => {
    # 用普通用户 token 调用 GET /api/admin/users
    # 验证: 状态码 403, 提示无权限
  });

  test('管理员 → 可访问管理接口', () => {
    # 用管理员 token 调用 GET /api/admin/users
    # 验证: 状态码 200, 返回用户列表
  });

  test('无 Token → 401 未授权', () => {
    # 不带 Authorization header 调用
    # 验证: 状态码 401
  });
});
```

### 功能点 2: 用户 CRUD

```python
describe('用户 CRUD', () => {
  test('查询用户列表 → 分页返回', () => {
    # GET /api/users?page=1&limit=20
    # 验证: 状态码 200, 返回 users[], total, page, limit
  });

  test('按用户名搜索', () => {
    # GET /api/users?search=张三
    # 验证: 返回的用户名都包含 "张三"
  });

  test('查询单个用户', () => {
    # GET /api/users/{user_id}
    # 验证: 返回该用户详细信息
  });

  test('查询不存在的用户 → 404', () => {
    # GET /api/users/999999
    # 验证: 状态码 404
  });

  test('创建用户', () => {
    # POST /api/users
    # body: { username, phone, email, role }
    # 验证: 状态码 201, 返回创建的用户信息
  });

  test('创建用户 - 用户名重复 → 400', () => {
    # POST /api/users
    # body: { username: 'existing' }
    # 验证: 状态码 400, 提示用户名已存在
  });

  test('更新用户信息', () => {
    # PUT /api/users/{user_id}
    # body: { email: 'new@example.com' }
    # 验证: 状态码 200, 返回更新后的用户
  });

  test('删除用户', () => {
    # DELETE /api/users/{user_id}
    # 验证: 状态码 204
    # 验证: 再次查询 → 404
  });

  test('删除自己 → 禁止', () => {
    # DELETE /api/users/{current_user_id}
    # 验证: 状态码 400, 提示不能删除自己
  });
});
```

### 功能点 3: 批量操作

```python
describe('批量操作', () => {
  test('批量删除用户', () => {
    # POST /api/users/batch-delete
    # body: { user_ids: [1, 2, 3] }
    # 验证: 状态码 200, 返回成功数量
    # 验证: 这些用户已被删除
  });

  test('批量更新角色', () => {
    # POST /api/users/batch-update
    # body: { user_ids: [1, 2], role: 'admin' }
    # 验证: 状态码 200
    # 验证: 这些用户的角色已变更
  });
});
```

---

## 商品管理模块测试

### 功能点 1: 商品 CRUD

```python
describe('商品 CRUD', () => {
  test('创建商品', () => {
    # POST /api/products
    # body: { name, price, category_id, sku: [...] }
    # 验证: 状态码 201, 返回商品信息含 product_id
  });

  test('创建商品 - 价格 <= 0 → 验证错误', () => {
    # POST /api/products
    # body: { name: 'test', price: 0 }
    # 验证: 状态码 422, 提示价格必须大于 0
  });

  test('查询商品列表', () => {
    # GET /api/products
    # 验证: 返回商品分页列表
  });

  test('按分类筛选', () => {
    # GET /api/products?category_id=1
    # 验证: 所有商品 category_id = 1
  });

  test('按价格区间筛选', () => {
    # GET /api/products?min_price=100&max_price=500
    # 验证: 所有商品价格在 100-500 之间
  });

  test('排序 (价格/销量/时间)', () => {
    # GET /api/products?sort=price_asc
    # 验证: 价格递增
    # GET /api/products?sort=sales_desc
    # 验证: 销量递减
  });

  test('查询单个商品', () => {
    # GET /api/products/{product_id}
    # 验证: 返回商品详情, 含 SKU 列表
  });
});
```

### 功能点 2: SKU 管理

```python
describe('SKU 管理', () => {
  test('商品添加 SKU 规格', () => {
    # POST /api/products/{product_id}/skus
    # body: { specs: { color: '黑色', storage: '256GB' }, price: 2999, stock: 100 }
    # 验证: 状态码 201, SKU 创建成功
  });

  test('SKU 库存不足 → 购买时提示', () => {
    # 设置某 SKU stock = 0
    # 尝试下单该 SKU
    # 验证: 提示库存不足
  });

  test('更新 SKU 价格', () => {
    # PUT /api/products/{product_id}/skus/{sku_id}
    # body: { price: 2599 }
    # 验证: 状态码 200, 价格已更新
  });

  test('删除 SKU', () => {
    # DELETE /api/products/{product_id}/skus/{sku_id}
    # 验证: 状态码 204
  });
});
```

### 功能点 3: 库存管理

```python
describe('库存管理', () => {
  test('入库 → 库存增加', () => {
    # POST /api/products/{product_id}/stock
    # body: { sku_id, quantity: 100, type: 'in' }
    # 验证: 库存增加 100
  });

  test('出库 → 库存减少', () => {
    # POST /api/products/{product_id}/stock
    # body: { sku_id, quantity: 10, type: 'out' }
    # 验证: 库存减少 10
  });

  test('出库数量 > 库存 → 失败', () => {
    # 当前库存 5, 尝试出库 10
    # 验证: 状态码 400, 提示库存不足
  });

  test('查询库存流水', () => {
    # GET /api/products/{product_id}/stock-log
    # 验证: 返回进出库记录列表
  });
});
```

---

## 订单模块测试

### 功能点 1: 创建订单

```python
describe('创建订单', () => {
  test('正常创建订单', () => {
    # POST /api/orders
    # body: { items: [{sku_id, quantity}], address: {...}, payment_method: 'wechat' }
    # 验证: 状态码 201, 返回 order_id, total_amount
  });

  test('SKU 不存在 → 400 错误', () => {
    # POST /api/orders
    # body: { items: [{sku_id: 99999}] }
    # 验证: 状态码 400, 提示商品不存在
  });

  test('数量超过库存 → 400 错误', () => {
    # 当前库存 10, 尝试购买 20
    # 验证: 状态码 400, 提示库存不足
  });

  test('地址信息不完整 → 422 验证错误', () => {
    # POST /api/orders
    # body: { items: [...], address: { name: '张三' } }  # 缺少手机号、地址
    # 验证: 状态码 422, 列出缺失字段
  });

  test('购物车已变更 → 创建失败', () => {
    # 用户 A 添加商品到购物车
    # 管理员修改了商品价格
    # 用户 A 尝试下单
    # 验证: 提示价格已变更, 需重新确认
  });
});
```

### 功能点 2: 订单查询

```python
describe('订单查询', () => {
  test('查询用户订单列表', () => {
    # GET /api/orders
    # 验证: 返回当前用户的订单列表
  });

  test('筛选状态 (待付款/待发货/已完成)', () => {
    # GET /api/orders?status=pending
    # 验证: 只返回待付款订单
  });

  test('按订单号搜索', () => {
    # GET /api/orders?order_no=xxx
    # 验证: 返回匹配的订单
  });

  test('查询订单详情', () => {
    # GET /api/orders/{order_id}
    # 验证: 返回订单详情含商品列表、地址、支付信息
  });

  test('禁止查看他人订单', () => {
    # 用户 A 尝试查询用户 B 的订单
    # 验证: 状态码 403
  });
});
```

### 功能点 3: 订单状态流转

```python
describe('订单状态流转', () => {
  test('创建订单 → 状态 pending (待付款)', () => {
    # POST /api/orders
    # 验证: order.status = 'pending'
  });

  test('支付成功 → 状态 paid (已付款)', () => {
    # POST /api/orders/{order_id}/pay
    # body: { payment_id: 'xxx' }
    # 验证: order.status = 'paid'
  });

  test('发货 → 状态 shipped (已发货)', () => {
    # POST /api/orders/{order_id}/ship
    # body: { tracking_number: 'SF123456' }
    # 验证: order.status = 'shipped', 物流单号已记录
  });

  test('确认收货 → 状态 completed (已完成)', () => {
    # POST /api/orders/{order_id}/receive
    # 验证: order.status = 'completed'
  });

  test('取消订单 (待付款) → 状态 cancelled', () => {
    # POST /api/orders/{order_id}/cancel
    # body: { reason: '不想要了' }
    # 验证: order.status = 'cancelled'
  });

  test('已发货订单 → 不可取消', () => {
    # 对已发货订单调用取消
    # 验证: 状态码 400, 提示已发货不可取消
  });
});
```

### 功能点 4: 退款

```python
describe('退款', () => {
  test('申请退款 → 状态 refunding', () => {
    # POST /api/orders/{order_id}/refund
    # body: { reason: '商品损坏' }
    # 验证: order.status = 'refunding'
  });

  test('管理员审核通过 → 退款完成', () => {
    # POST /api/orders/{order_id}/refund/approve
    # 验证: order.status = 'refunded'
  });

  test('管理员审核拒绝 → 状态恢复', () => {
    # POST /api/orders/{order_id}/refund/reject
    # body: { reason: '不符合退款条件' }
    # 验证: order.status 恢复为之前状态
  });

  test('退款进度查询', () => {
    # GET /api/orders/{order_id}/refund-status
    # 验证: 返回退款流程状态
  });
});
```

---

## 通用测试场景

### 功能点: 安全

```python
describe('安全', () => {
  test('SQL 注入防护', () => {
    # GET /api/users?search='; DROP TABLE users; --
    # 验证: 无 SQL 注入, 正常返回 (当作普通搜索词)
  });

  test('XSS 防护', () => {
    # POST /api/users
    # body: { username: '<script>alert(1)</script>' }
    # 验证: 内容被转义存储, 返回时不会被执行
  });

  test('频率限制 → 超过阈值返回 429', () => {
    # 循环调用接口 100 次
    # 验证: 超过限制后返回 429 Too Many Requests
  });

  test('CORS 头设置正确', () => {
    # 跨域请求
    # 验证: 响应头包含正确的 Access-Control-Allow-Origin
  });
});
```

### 功能点: 接口幂等性

```python
describe('幂等性', () => {
  test('重复创建订单 → 返回同一订单', () => {
    # 构造两次相同的订单请求 (使用 idempotency_key)
    # 验证: 第二次返回相同的 order_id, 不重复创建
  });

  test('重复支付 → 只扣一次钱', () => {
    # 对同一订单发起两次支付
    # 验证: 只会扣一次钱, 第二次返回"已支付"
  });
});
```

### 功能点: 并发

```python
describe('并发', () => {
  test('库存扣减并发 → 不超卖', () => {
    # 100 个并发请求购买库存为 10 的商品
    # 验证: 最终售出 10 件, 剩余 0 件, 90 个请求失败
  });

  test('并发创建订单 → 数据一致', () => {
    # 并发创建订单
    # 验证: 所有订单数据一致, 无数据竞争
  });
});
```

---

## 测试脚本结构模板

```python
# test_{module}.py
import pytest

class TestAuth:
  """用户认证测试"""

  @pytest.fixture(autouse=True)
  def setup(self):
    # 每个测试前执行: 清理数据, 创建测试用户
    pass

  def test_login_success(self):
    # Arrange: 准备测试数据
    # Act: 调用接口
    # Assert: 验证响应

  def test_login_invalid_password(self):
    pass

class TestUsers:
  """用户管理测试"""

  def test_list_users(self):
    pass

  def test_create_user_duplicate(self):
    pass
```

---

## pytest 常用技巧

```python
# 使用 fixture 共享测试数据
@pytest.fixture
def admin_token():
  return get_token('admin', 'password')

# 参数化测试
@pytest.mark.parametrize('status', ['pending', 'paid', 'shipped', 'completed'])
def test_order_status(status):
  pass

# 跳过某些测试
@pytest.mark.skip(reason='等待第三方接口')
def test_external_api():
  pass

# 预期失败
@pytest.mark.xfail(reason='已知 bug')
def test_known_bug():
  pass

# 使用 Faker 生成测试数据
from faker import Faker
fake = Faker()

def test_create_user():
  user = {
    'name': fake.name(),
    'email': fake.email(),
    'phone': fake.phone_number()
  }
```

---

## 验证断言示例

```python
# 状态码断言
assert response.status_code == 200
assert response.status_code == 201

# JSON 字段断言
assert response.json()['user_id'] == 123
assert response.json()['token'] is not None

# 列表断言
assert len(response.json()['users']) == 20
assert response.json()['total'] > 0

# 错误响应断言
assert response.status_code == 400
assert 'error' in response.json()
assert response.json()['error']['code'] == 'USER_EXISTS'

# 分页断言
assert 'page' in response.json()
assert 'limit' in response.json()
assert 'total' in response.json()

# 时间格式断言
from datetime import datetime
date = datetime.fromisoformat(response.json()['created_at'])
assert date.year == 2024
```

---

## 前端 E2E 测试伪代码示例

见 `frontend-e2e-example.md`