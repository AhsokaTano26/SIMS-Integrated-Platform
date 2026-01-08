<template>
  <div class="dashboard">
    <el-header style="background: #67C23A; color: white; line-height: 60px;">
      辅导员管理后台
    </el-header>
    <el-main>
      <el-alert title="欢迎回来，老师。您可以在此审批学生请假和查看异常考勤。" type="success" :closable="false" />
      <el-table :data="[]" style="width: 100%; margin-top: 20px">
        <el-table-column prop="student" label="学生姓名" />
        <el-table-column prop="type" label="预警类型" />
        <el-table-column label="操作">
          <template #default>
            <el-button link type="primary">查看详情</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-main>
  </div>
</template>
