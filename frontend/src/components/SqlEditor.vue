<template>
  <div ref="editorHost" class="sql-editor"></div>
</template>

<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { basicSetup, EditorView } from 'codemirror'
import { EditorState } from '@codemirror/state'
import { sql, PostgreSQL } from '@codemirror/lang-sql'
import { oneDark } from '@codemirror/theme-one-dark'

const props = defineProps<{ modelValue: string }>()
const emit = defineEmits<{ 'update:modelValue': [value: string]; execute: [] }>()
const editorHost = ref<HTMLElement>()
let view: EditorView | undefined

onMounted(() => {
  if (!editorHost.value) return
  view = new EditorView({
    parent: editorHost.value,
    state: EditorState.create({
      doc: props.modelValue,
      extensions: [
        basicSetup,
        sql({ dialect: PostgreSQL }),
        oneDark,
        EditorView.lineWrapping,
        EditorView.updateListener.of((update) => {
          if (update.docChanged) emit('update:modelValue', update.state.doc.toString())
        }),
        EditorView.domEventHandlers({
          keydown(event) {
            if ((event.ctrlKey || event.metaKey) && event.key === 'Enter') {
              event.preventDefault()
              emit('execute')
              return true
            }
            return false
          },
        }),
        EditorView.theme({
          '&': { height: '230px', backgroundColor: '#071522' },
          '.cm-scroller': { fontFamily: "'DM Mono', monospace", fontSize: '13px', lineHeight: '1.75' },
          '.cm-gutters': { backgroundColor: '#091827', borderRight: '1px solid rgba(151,179,207,.1)', color: '#405a71' },
          '.cm-activeLine, .cm-activeLineGutter': { backgroundColor: 'rgba(41,216,199,.035)' },
          '.cm-content': { padding: '13px 0' },
        }),
      ],
    }),
  })
})

watch(() => props.modelValue, (value) => {
  if (!view || view.state.doc.toString() === value) return
  view.dispatch({ changes: { from: 0, to: view.state.doc.length, insert: value } })
})

onBeforeUnmount(() => view?.destroy())
</script>

<style scoped>
.sql-editor { overflow: hidden; border-radius: 7px; border: 1px solid rgba(151,179,207,.12); }
</style>
