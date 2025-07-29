# MCP工具调用提示词指导

这份指导帮助你在MCP客户端（如Claude Desktop、Cherry Studio等）中有效使用Java依赖分析工具。

## 🎯 基本原则

### 1. 明确目标
- **具体说明你想要分析什么**
- **指明项目仓库地址**
- **描述你关心的方面**

### 2. 提供上下文
- 说明你的使用场景
- 提及你的技术背景
- 指出特别关注的问题

### 3. 指导工具选择
- 建议使用哪些MCP工具
- 说明分析的优先级

## 📝 提示词模板

### 🔍 **场景1：项目依赖分析**

#### 基础版本
```
请帮我分析GitHub项目 yangzongzhuan/RuoYi 的Java依赖关系，我想了解：
1. 这个项目用了哪些主要的第三方库
2. 依赖的技术栈是什么
3. 有没有潜在的安全风险

请使用 analyze_java_dependencies 工具进行分析。
```

#### 详细版本
```
我正在评估一个Java管理系统项目 yangzongzhuan/RuoYi，准备用于公司内部开发。

请帮我全面分析这个项目的依赖情况：

1. **依赖概览**：使用 analyze_java_dependencies 分析所有依赖
2. **技术栈评估**：重点关注Spring、MyBatis等框架版本
3. **安全性检查**：是否有已知漏洞的依赖版本
4. **维护性评估**：依赖库的活跃度和更新频率

我特别关心：
- Spring Boot版本是否是LTS版本
- 数据库连接池的选择
- 安全框架的配置

请按优先级给出分析结果和建议。
```

### 🔎 **场景2：方法实现追踪**

#### 基础版本
```
在RuoYi项目中，我看到很多地方用了 StrUtil.format 方法，请帮我追踪这个方法的具体实现，我想知道：
1. 这个方法来自哪个依赖库
2. 具体的实现代码是什么
3. 在项目中哪些地方使用了它

请使用 trace_method_implementation 工具分析 yangzongzhuan/RuoYi 项目中的 StrUtil.format 方法。
```

#### 详细版本
```
我在研究Java项目 yangzongzhuan/RuoYi 中的字符串处理逻辑，发现大量使用了工具类方法。

请帮我深入追踪以下方法的实现：

**主要目标**：StrUtil.format
**仓库**：yangzongzhuan/RuoYi

**分析需求**：
1. **来源追踪**：这个方法来自哪个jar包？是Hutool吗？
2. **实现细节**：具体的源码实现逻辑
3. **使用模式**：在RuoYi项目中如何被调用的
4. **替代方案**：如果要替换这个方法，有什么其他选择

**额外分析**（如果时间允许）：
- 同时分析 StrUtil.isEmpty 方法
- 比较与 Apache Commons StringUtils 的差异

请使用 trace_method_implementation 工具，并给出详细的分析报告。
```

### 🔗 **场景3：依赖链分析**

#### 基础版本
```
请分析Hutool工具库中 StrUtil 类的完整依赖链，我想了解它最终依赖了哪些基础库。

使用 analyze_dependency_chain 工具分析 dromara/hutool 项目中的 StrUtil 类。
```

#### 详细版本
```
我正在做Java工具库的技术调研，想深入了解Hutool的StrUtil类的设计架构。

**分析目标**：
- 仓库：dromara/hutool
- 目标类：StrUtil

**分析重点**：
1. **依赖层次**：StrUtil依赖了哪些其他类？
2. **基础依赖**：最终依赖到JDK的哪些核心类？
3. **设计模式**：从依赖关系看出的设计思路
4. **复杂度评估**：依赖链的深度和复杂程度

请使用 analyze_dependency_chain 工具进行深度分析，并给出架构设计的评价。

**附加需求**：如果可能，也分析一下 DateUtil 类作为对比。
```

### 🛡️ **场景4：安全代码审查**

#### 基础版本
```
请对项目 yangzongzhuan/RuoYi 进行安全性代码审查，重点关注潜在的安全漏洞。

使用 smart_code_review 工具，设置 focus_area 为 "security"。
```

#### 详细版本
```
我需要对一个准备上线的Java管理系统进行安全评估。

**项目信息**：
- 仓库：yangzongzhuan/RuoYi
- 项目类型：Spring Boot Web应用
- 部署环境：生产环境

**安全审查要求**：
1. **输入验证**：SQL注入、XSS等常见攻击防护
2. **权限控制**：认证授权机制的实现
3. **敏感信息**：密码、密钥等信息的处理
4. **依赖安全**：第三方库的安全漏洞

**审查优先级**：
- 高：认证、授权、SQL操作相关代码
- 中：文件上传、数据导出功能
- 低：日志记录、工具类方法

请使用 smart_code_review 工具，focus_area 设为 "security"，max_files 设为 8，进行深度安全审查。

**期望输出**：
- 发现的安全问题分级列表
- 具体的修复建议
- 安全最佳实践推荐
```

### 🚀 **场景5：性能优化审查**

#### 基础版本
```
请帮我分析项目 dromara/hutool 的性能相关代码，找出可能的性能瓶颈。

使用 smart_code_review 工具，focus_area 设为 "performance"。
```

#### 详细版本
```
我在使用Hutool工具库时遇到了性能问题，想了解是否有优化空间。

**分析目标**：
- 仓库：dromara/hutool
- 关注点：性能优化

**具体需求**：
1. **算法效率**：核心工具方法的算法复杂度
2. **内存使用**：是否有内存泄漏或不当的对象创建
3. **并发安全**：多线程环境下的性能表现
4. **缓存机制**：是否合理使用了缓存

**重点分析类**：
- StrUtil（字符串处理）
- DateUtil（日期处理）
- CollUtil（集合处理）

请使用 smart_code_review 工具，focus_area 为 "performance"，max_files 为 10。

**期望得到**：
- 性能热点识别
- 优化建议
- 与同类库的性能对比分析
```

## 🎨 高级技巧

### 1. 组合使用多个工具
```
我想全面了解项目 yangzongzhuan/RuoYi，请按以下步骤分析：

第一步：使用 analyze_java_dependencies 了解整体依赖情况
第二步：使用 trace_method_implementation 追踪核心工具方法 StrUtil.format
第三步：使用 smart_code_review 进行安全性审查（focus_area: security）
第四步：总结分析结果，给出项目评估报告

请逐步执行，每个步骤完成后暂停，等待我确认再继续下一步。
```

### 2. 指定输出格式
```
请分析项目 dromara/hutool 的依赖关系，并按以下格式输出：

## 项目概览
- 项目类型：
- 依赖总数：
- 主要技术栈：

## 核心依赖（前10个）
| 组织 | 组件 | 版本 | 用途 |
|------|------|------|------|

## 风险评估
- 高风险依赖：
- 版本过时依赖：
- 建议升级：

使用 analyze_java_dependencies 工具进行分析。
```

### 3. 比较分析
```
请比较分析两个字符串工具库的设计差异：

1. **Hutool的StrUtil**（dromara/hutool 项目）
2. **Apache Commons的StringUtils**（在 yangzongzhuan/RuoYi 项目中的使用）

对比维度：
- 功能完整性（使用 trace_method_implementation）
- 依赖复杂度（使用 analyze_dependency_chain）  
- 性能表现（使用 smart_code_review performance模式）

请分别分析后给出选择建议。
```

## ✅ 最佳实践

### ✅ 好的提示词特征
- **具体明确**：指明具体的仓库和分析目标
- **结构清晰**：使用编号、分点说明需求
- **工具明确**：指出要使用的MCP工具
- **背景充分**：说明分析的目的和场景
- **优先级明确**：指出重点关注的方面

### ❌ 避免的问题
- **过于模糊**："帮我看看这个项目"
- **目标不明**：不说明要分析什么方面
- **信息不足**：不提供仓库地址或具体方法名
- **要求过多**：一次性要求分析太多内容
- **格式混乱**：没有清晰的结构

## 🔧 故障排除

### 如果工具调用失败
```
如果工具调用遇到错误，请：
1. 先使用 check_file_exists 确认仓库和文件是否存在
2. 使用 get_repository_structure 了解项目结构
3. 简化分析要求，逐步深入

请帮我检查仓库 yangzongzhuan/RuoYi 是否可以访问，然后再进行依赖分析。
```

### 获取更多信息
```
在分析过程中如果需要更多项目信息，请：
1. 使用 get_repository_info 获取基本信息
2. 使用 get_file_content 查看具体配置文件
3. 使用 search_code 搜索特定代码模式

请先了解项目基本情况，再开始依赖分析。
```

这份指导应该能帮你写出高效的MCP工具调用提示词！ 