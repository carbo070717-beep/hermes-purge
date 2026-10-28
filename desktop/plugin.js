/**
 * hermes-purge — Desktop management UI
 *
 * Adapted from dsh-purge's client.js (React component for DSH web client)
 * to the Hermes desktop plugin SDK.
 *
 * Provides a pane with:
 *   - Status overview (override, rules, presets, identity, drill grant)
 *   - System prompt override editor
 *   - Rules list
 *   - Presets list
 *   - Identity editor
 *   - Red-team console (drill grant, targets)
 *
 * The backend is at /api/plugins/hermes-purge/ (plugin_api.py).
 */

import {
  cn, Button, Input, Textarea, Badge, Tip, Tabs, TabList,
  usePluginI18n, host,
} from '@hermes/plugin-sdk'
import { jsx, jsxs } from 'react/jsx-runtime'
import { useState, useEffect } from 'react'

const ID = 'hermes-purge'

// Module-level ctx reference (set in register(), used by components)
let _ctx = null

/** Call the plugin's Python backend via ctx.rest() */
async function api(path, method = 'GET', body = null) {
  if (!_ctx) throw new Error('hermes-purge: ctx not available yet')
  const opts = { method, timeoutMs: 30000 }
  if (body) opts.body = body
  return _ctx.rest(path, opts)
}

// ---------------------------------------------------------------------------
// Status Overview
// ---------------------------------------------------------------------------

function StatusOverview({ status, refresh }) {
  const t = usePluginI18n(ID)
  if (!status) return jsx('div', { className: 'p-3 text-sm text-(--ui-text-tertiary)', children: 'Loading…' })

  return jsxs('div', {
    className: 'flex flex-col gap-3 p-3 text-sm',
    children: [
      jsxs('div', {
        className: 'flex items-center justify-between',
        children: [
          jsx('span', { className: 'font-medium', children: t('status.title') }),
          jsx(Button, {
            size: 'sm',
            variant: 'secondary',
            onClick: refresh,
            children: t('status.refresh'),
          }),
        ],
      }),
      jsxs('div', { className: 'grid grid-cols-2 gap-2', children: [
        jsx('div', { className: 'rounded-lg bg-(--ui-bg-secondary) p-2', children: jsxs('div', { children: [
          jsx('div', { className: 'text-(--ui-text-tertiary) text-xs', children: t('status.override') }),
          jsx('div', { className: 'font-medium', children: status.has_override ? t('status.applied') : t('status.default') }),
        ]})}),
        jsx('div', { className: 'rounded-lg bg-(--ui-bg-secondary) p-2', children: jsxs('div', { children: [
          jsx('div', { className: 'text-(--ui-text-tertiary) text-xs', children: t('status.rules') }),
          jsx('div', { className: 'font-medium', children: String(status.rules_count) }),
        ]})}),
        jsx('div', { className: 'rounded-lg bg-(--ui-bg-secondary) p-2', children: jsxs('div', { children: [
          jsx('div', { className: 'text-(--ui-text-tertiary) text-xs', children: t('status.presets') }),
          jsx('div', { className: 'font-medium', children: String(status.presets_count) }),
        ]})}),
        jsx('div', { className: 'rounded-lg bg-(--ui-bg-secondary) p-2', children: jsxs('div', { children: [
          jsx('div', { className: 'text-(--ui-text-tertiary) text-xs', children: t('status.identity') }),
          jsx('div', { className: 'font-medium truncate', children: status.identity?.name || t('status.none') }),
        ]})}),
      ]}),
      status.drill_granted
        ? jsx(Badge, { variant: 'default', children: t('status.drillGranted') })
        : jsx(Badge, { variant: 'outline', children: t('status.drillNotGranted') }),
      jsx('div', {
        className: 'rounded-lg bg-(--ui-bg-secondary) p-2 text-xs text-(--ui-text-tertiary)',
        children: status.effective_prompt_preview
      }),
    ],
  })
}

// ---------------------------------------------------------------------------
// Override Editor
// ---------------------------------------------------------------------------

function OverrideEditor({ override, onSave, onRevert }) {
  const t = usePluginI18n(ID)
  const [text, setText] = useState(override || '')

  return jsxs('div', {
    className: 'flex flex-col gap-2 p-3 text-sm',
    children: [
      jsx('div', { className: 'font-medium', children: t('override.title') }),
      jsx(Textarea, {
        value: text,
        onChange: e => setText(e.target.value),
        rows: 8,
        placeholder: t('override.placeholder'),
        className: 'font-mono text-xs',
      }),
      jsxs('div', { className: 'flex gap-2', children: [
        jsx(Button, {
          size: 'sm',
          onClick: () => onSave(text),
          children: t('override.save'),
        }),
        jsx(Button, {
          size: 'sm',
          variant: 'secondary',
          onClick: onRevert,
          children: t('override.revert'),
        }),
      ]}),
    ],
  })
}

// ---------------------------------------------------------------------------
// Rules List
// ---------------------------------------------------------------------------

function RulesList({ rules, onRemove }) {
  const t = usePluginI18n(ID)
  if (!rules || rules.length === 0) {
    return jsx('div', { className: 'p-3 text-sm text-(--ui-text-tertiary)', children: t('rules.empty') })
  }

  return jsx('div', { className: 'flex flex-col gap-1 p-3 text-sm', children:
    rules.map(rule => jsxs('div', {
      className: 'flex items-center justify-between rounded-lg bg-(--ui-bg-secondary) p-2',
      children: [
        jsxs('div', { className: 'flex-1', children: [
          jsx('div', { className: 'font-medium', children: rule.name }),
          jsx('div', { className: 'text-xs text-(--ui-text-tertiary) truncate', children: (rule.prompt || '').slice(0, 80) }),
        ]}),
        jsx(Button, {
          size: 'sm',
          variant: 'ghost',
          onClick: () => onRemove(rule.name),
          children: t('rules.remove'),
        }),
      ],
    }))
  })
}

// ---------------------------------------------------------------------------
// Presets List
// ---------------------------------------------------------------------------

function PresetsList({ presets, onApply }) {
  const t = usePluginI18n(ID)
  if (!presets || presets.length === 0) {
    return jsx('div', { className: 'p-3 text-sm text-(--ui-text-tertiary)', children: t('presets.empty') })
  }

  return jsx('div', { className: 'flex flex-col gap-1 p-3 text-sm', children:
    presets.map(preset => jsxs('div', {
      className: 'flex items-center justify-between rounded-lg bg-(--ui-bg-secondary) p-2',
      children: [
        jsxs('div', { className: 'flex-1', children: [
          jsx('div', { className: 'font-medium', children: preset.name }),
          jsx('div', { className: 'text-xs text-(--ui-text-tertiary) truncate', children: (preset.override || '').slice(0, 80) }),
        ]}),
        jsx(Button, {
          size: 'sm',
          variant: 'ghost',
          onClick: () => onApply(preset.name),
          children: t('presets.apply'),
        }),
      ],
    }))
  })
}

// ---------------------------------------------------------------------------
// Identity Editor
// ---------------------------------------------------------------------------

function IdentityEditor({ identity, onSave }) {
  const t = usePluginI18n(ID)
  const [name, setName] = useState(identity?.name || '')
  const [desc, setDesc] = useState(identity?.description || '')

  return jsxs('div', {
    className: 'flex flex-col gap-2 p-3 text-sm',
    children: [
      jsx('div', { className: 'font-medium', children: t('identity.title') }),
      jsx(Input, {
        value: name,
        onChange: e => setName(e.target.value),
        placeholder: t('identity.name'),
      }),
      jsx(Input, {
        value: desc,
        onChange: e => setDesc(e.target.value),
        placeholder: t('identity.desc'),
      }),
      jsx(Button, {
        size: 'sm',
        onClick: () => onSave(name, desc),
        children: t('identity.save'),
      }),
    ],
  })
}

// ---------------------------------------------------------------------------
// Red Team Console
// ---------------------------------------------------------------------------

function RedTeamConsole({ granted, onGrant, onRevoke, targets, onAddTarget, onRemoveTarget }) {
  const t = usePluginI18n(ID)
  const [target, setTarget] = useState('')

  return jsxs('div', {
    className: 'flex flex-col gap-2 p-3 text-sm',
    children: [
      jsx('div', { className: 'font-medium', children: t('redteam.title') }),
      jsx('div', {
        className: 'rounded-lg bg-(--ui-bg-warning) p-2 text-xs',
        children: t('redteam.warning'),
      }),
      jsxs('div', { className: 'flex items-center gap-2', children: [
        jsx('span', { children: t('redteam.grant') }),
        granted
          ? jsx(Button, { size: 'sm', variant: 'secondary', onClick: onRevoke, children: t('redteam.revoke') })
          : jsx(Button, { size: 'sm', onClick: onGrant, children: t('redteam.grantBtn') }),
      ]}),
      jsx('div', { className: 'font-medium mt-2', children: t('redteam.targets') }),
      jsxs('div', { className: 'flex gap-2', children: [
        jsx(Input, {
          value: target,
          onChange: e => setTarget(e.target.value),
          placeholder: t('redteam.targetPlaceholder'),
          className: 'flex-1',
        }),
        jsx(Button, {
          size: 'sm',
          onClick: () => { if (target) { onAddTarget(target); setTarget('') } },
          children: t('redteam.add'),
        }),
      ]}),
      targets && targets.length > 0
        ? jsx('div', { className: 'flex flex-col gap-1', children:
          targets.map(tgt => jsxs('div', {
            className: 'flex items-center justify-between rounded bg-(--ui-bg-secondary) px-2 py-1',
            children: [
              jsx('span', { className: 'text-xs', children: tgt }),
              jsx(Button, {
                size: 'sm',
                variant: 'ghost',
                onClick: () => onRemoveTarget(tgt),
                children: t('redteam.remove'),
              }),
            ],
          }))
        })
        : jsx('div', { className: 'text-xs text-(--ui-text-tertiary)', children: t('redteam.noTargets') }),
    ],
  })
}

// ---------------------------------------------------------------------------
// Main Pane Component
// ---------------------------------------------------------------------------

function PurgePane() {
  const t = usePluginI18n(ID)
  const [activeTab, setActiveTab] = useState('status')
  const [status, setStatus] = useState(null)
  const [override, setOverride] = useState('')
  const [rules, setRules] = useState([])
  const [presets, setPresets] = useState([])
  const [identity, setIdentity] = useState(null)
  const [drillGranted, setDrillGranted] = useState(false)
  const [targets, setTargets] = useState([])

  const refreshAll = async () => {
    try {
      const [s, r, p, i, rt] = await Promise.all([
        api('/status'),
        api('/rules'),
        api('/presets'),
        api('/identity'),
        api('/redteam'),
      ])
      setStatus(s)
      setOverride((await api('/override')).text || '')
      setRules(r.rules || [])
      setPresets(p.presets || [])
      setIdentity(i)
      setDrillGranted(rt.granted || false)
      setTargets(rt.targets || [])
    } catch (e) {
      console.error('hermes-purge: refresh failed', e)
    }
  }

  // Initial load
  useEffect(() => { refreshAll() }, [])

  // Poll every 5s
  useEffect(() => {
    const interval = setInterval(refreshAll, 5000)
    return () => clearInterval(interval)
  }, [])

  const doSaveOverride = async (text) => {
    await api('/override', 'POST', { op: 'save', text })
    host.notify({ kind: 'success', message: t('override.saved') })
    refreshAll()
  }

  const doRevert = async () => {
    await api('/override', 'POST', { op: 'revert' })
    host.notify({ kind: 'info', message: t('override.reverted') })
    refreshAll()
  }

  const doRemoveRule = async (name) => {
    await api('/rules', 'POST', { op: 'remove', name })
    refreshAll()
  }

  const doApplyPreset = async (name) => {
    await api('/presets', 'POST', { op: 'apply', name })
    host.notify({ kind: 'success', message: t('presets.applied') })
    refreshAll()
  }

  const doSaveIdentity = async (name, desc) => {
    await api('/identity', 'POST', { name, description: desc })
    host.notify({ kind: 'success', message: t('identity.saved') })
    refreshAll()
  }

  const doGrant = async () => {
    await api('/grant', 'POST', { granted: true })
    refreshAll()
  }

  const doRevoke = async () => {
    await api('/grant', 'POST', { granted: false })
    refreshAll()
  }

  const doAddTarget = async (target) => {
    try {
      await api('/redteam/targets', 'POST', { op: 'add', target })
      host.notify({ kind: 'success', message: t('redteam.targetAdded') })
      refreshAll()
    } catch (e) {
      host.notify({ kind: 'error', message: e.message || String(e) })
    }
  }

  const doRemoveTarget = async (target) => {
    await api('/redteam/targets', 'POST', { op: 'remove', target })
    refreshAll()
  }

  return jsx('div', { className: 'flex h-full flex-col text-sm', children:
    jsxs(Tabs, {
      value: activeTab,
      onValueChange: setActiveTab,
      children: [
        jsx(TabList, { className: 'flex border-b border-(--ui-stroke-secondary)', children: [
          jsx(Tabs.Tab, { value: 'status', children: t('tabs.status') }),
          jsx(Tabs.Tab, { value: 'override', children: t('tabs.override') }),
          jsx(Tabs.Tab, { value: 'rules', children: t('tabs.rules') }),
          jsx(Tabs.Tab, { value: 'presets', children: t('tabs.presets') }),
          jsx(Tabs.Tab, { value: 'identity', children: t('tabs.identity') }),
          jsx(Tabs.Tab, { value: 'redteam', children: t('tabs.redteam') }),
        ]}),
        activeTab === 'status'
          ? jsx(StatusOverview, { status, refresh: refreshAll })
          : null,
        activeTab === 'override'
          ? jsx(OverrideEditor, { override, onSave: doSaveOverride, onRevert: doRevert })
          : null,
        activeTab === 'rules'
          ? jsx(RulesList, { rules, onRemove: doRemoveRule })
          : null,
        activeTab === 'presets'
          ? jsx(PresetsList, { presets, onApply: doApplyPreset })
          : null,
        activeTab === 'identity'
          ? jsx(IdentityEditor, { identity, onSave: doSaveIdentity })
          : null,
        activeTab === 'redteam'
          ? jsx(RedTeamConsole, {
              granted: drillGranted, onGrant: doGrant, onRevoke: doRevoke,
              targets, onAddTarget: doAddTarget, onRemoveTarget: doRemoveTarget,
            })
          : null,
      ],
    })
  })
}

// ---------------------------------------------------------------------------
// Status Bar Chip
// ---------------------------------------------------------------------------

function PurgeChip() {
  const t = usePluginI18n(ID)
  return jsx(Tip, {
    label: t('chipTip'),
    children: jsx('button', {
      className: cn(
        'inline-flex h-full items-center gap-1 px-1.5 text-[0.6875rem] transition-colors',
        'text-(--ui-text-tertiary) hover:bg-(--chrome-action-hover) hover:text-foreground'
      ),
      type: 'button',
      onClick: () => host.notify({ kind: 'info', message: t('chipMessage') }),
      children: 'hermes-purge'
    })
  })
}

// ---------------------------------------------------------------------------
// Plugin export
// ---------------------------------------------------------------------------

export default {
  id: ID,
  name: 'hermes-purge',
  register(ctx) {
    _ctx = ctx
    ctx.i18n.register({
      en: {
        'tabs.status': 'Status',
        'tabs.override': 'Override',
        'tabs.rules': 'Rules',
        'tabs.presets': 'Presets',
        'tabs.identity': 'Identity',
        'tabs.redteam': 'Red Team',
        'status.title': 'hermes-purge Status',
        'status.refresh': 'Refresh',
        'status.override': 'Override',
        'status.applied': 'Applied',
        'status.default': 'Default',
        'status.rules': 'Rules',
        'status.presets': 'Presets',
        'status.identity': 'Identity',
        'status.none': 'None',
        'status.drillGranted': 'Drill Granted',
        'status.drillNotGranted': 'Drill Not Granted',
        'override.title': 'System Prompt Override',
        'override.placeholder': 'Enter custom system prompt…',
        'override.save': 'Save',
        'override.revert': 'Revert',
        'override.saved': 'Override saved',
        'override.reverted': 'Reverted to default',
        'rules.empty': 'No rules yet',
        'rules.remove': 'Remove',
        'presets.empty': 'No presets saved',
        'presets.apply': 'Apply',
        'presets.applied': 'Preset applied',
        'identity.title': 'Identity',
        'identity.name': 'Name',
        'identity.desc': 'Description',
        'identity.save': 'Save',
        'identity.saved': 'Identity saved',
        'redteam.title': 'Red Team Console',
        'redteam.warning': '⚠ Drill targets must be local (loopback/RFC1918). Unauthorized use is prohibited.',
        'redteam.grant': 'Drill Authorization',
        'redteam.grantBtn': 'Grant',
        'redteam.revoke': 'Revoke',
        'redteam.targets': 'Drill Targets',
        'redteam.targetPlaceholder': 'IP or hostname (e.g. 127.0.0.1)',
        'redteam.add': 'Add',
        'redteam.remove': 'Remove',
        'redteam.noTargets': 'No targets registered',
        'redteam.targetAdded': 'Target added',
        'chipTip': 'hermes-purge — prompt management & red-team console',
        'chipMessage': 'Open hermes-purge panel from the sidebar',
      },
      zh: {
        'tabs.status': '状态',
        'tabs.override': '提示词',
        'tabs.rules': '规则',
        'tabs.presets': '预设',
        'tabs.identity': '身份',
        'tabs.redteam': '红队',
        'status.title': 'hermes-purge 状态',
        'status.refresh': '刷新',
        'status.override': '覆盖提示词',
        'status.applied': '已应用',
        'status.default': '默认',
        'status.rules': '规则数',
        'status.presets': '预设数',
        'status.identity': '身份',
        'status.none': '无',
        'status.drillGranted': '已授权',
        'status.drillNotGranted': '未授权',
        'override.title': '系统提示词覆盖',
        'override.placeholder': '输入自定义系统提示词…',
        'override.save': '保存',
        'override.revert': '恢复默认',
        'override.saved': '已保存',
        'override.reverted': '已恢复默认',
        'rules.empty': '暂无规则',
        'rules.remove': '删除',
        'presets.empty': '暂无预设',
        'presets.apply': '应用',
        'presets.applied': '预设已应用',
        'identity.title': '身份',
        'identity.name': '名称',
        'identity.desc': '描述',
        'identity.save': '保存',
        'identity.saved': '身份已保存',
        'redteam.title': '红队演练台',
        'redteam.warning': '⚠ 演练目标仅限本机回环和 RFC1918 私网。禁止未授权使用。',
        'redteam.grant': '演练授权',
        'redteam.grantBtn': '授权',
        'redteam.revoke': '撤销',
        'redteam.targets': '演练目标',
        'redteam.targetPlaceholder': 'IP 或主机名（如 127.0.0.1）',
        'redteam.add': '添加',
        'redteam.remove': '删除',
        'redteam.noTargets': '暂无目标',
        'redteam.targetAdded': '目标已添加',
        'chipTip': 'hermes-purge — 提示词管理与红队演练台',
        'chipMessage': '从侧边栏打开 hermes-purge 面板',
      },
    })

    // Management pane
    ctx.register({
      id: 'pane',
      area: 'panes',
      title: 'hermes-purge',
      data: { placement: 'right', width: '320px' },
      render: () => jsx(PurgePane, {}),
    })

    // Status bar chip
    ctx.register({
      id: 'chip',
      area: 'statusBar.right',
      order: 140,
      render: () => jsx(PurgeChip, {}),
    })
  },
}
