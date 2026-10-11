<template>
  <div class="map-page">
    <div class="map-toolbar panel">
      <div class="map-heading"><span>CHENGDU · WGS 84 / EPSG:4326</span><strong>高校图书馆空间分布 · {{ scopeLabel }}</strong></div>
      <div class="map-actions">
        <el-select v-model="selectedCampus" clearable filterable placeholder="定位校区" style="width: 190px" @change="focusCampus">
          <el-option v-for="campus in campusRows" :key="Number(campus.campus_id)" :label="String(campus.campus_name)" :value="Number(campus.campus_id)" />
        </el-select>
        <el-button :loading="loading" @click="loadMapData"><el-icon><Refresh /></el-icon>刷新图层</el-button>
      </div>
    </div>

    <div class="map-layout">
      <aside class="map-sidebar panel">
        <div class="panel-header"><div class="panel-title">图层控制</div></div>
        <div class="layer-list">
          <label><span><i class="legend-area site"></i>站点管理范围</span><el-switch v-model="visibility.sites" @change="syncVisibility" /></label>
          <label><span><i class="legend-area campus"></i>校区边界</span><el-switch v-model="visibility.campuses" @change="syncVisibility" /></label>
          <label><span><i class="legend-point"></i>图书馆位置</span><el-switch v-model="visibility.libraries" @change="syncVisibility" /></label>
        </div>
        <div class="map-statistics">
          <div><strong>{{ siteRows.length }}</strong><span>管理站点</span></div><div><strong>{{ campusRows.length }}</strong><span>高校校区</span></div><div><strong>{{ libraryRows.length }}</strong><span>图书馆</span></div>
        </div>
        <div class="selected-feature">
          <span>要素信息</span>
          <template v-if="selectedFeature">
            <strong>{{ selectedFeature.name }}</strong>
            <dl><template v-for="(value, key) in selectedFeature.properties" :key="key"><dt>{{ key }}</dt><dd>{{ value }}</dd></template></dl>
          </template>
          <p v-else>在地图上点击校区、站点范围或图书馆标记查看属性。</p>
        </div>
      </aside>
      <section class="map-canvas panel">
        <div ref="mapElement" class="map-host"></div>
        <div class="map-corner"><span><i></i>PostGIS LIVE DATA</span><small>OpenStreetMap · OpenLayers</small></div>
        <div v-if="errorMessage" class="map-error">{{ errorMessage }}</div>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import { Refresh } from '@element-plus/icons-vue'
import Map from 'ol/Map'
import View from 'ol/View'
import TileLayer from 'ol/layer/Tile'
import VectorLayer from 'ol/layer/Vector'
import OSM from 'ol/source/OSM'
import VectorSource from 'ol/source/Vector'
import GeoJSON from 'ol/format/GeoJSON'
import Feature from 'ol/Feature'
import Point from 'ol/geom/Point'
import { fromLonLat } from 'ol/proj'
import { Circle as CircleStyle, Fill, Stroke, Style, Text } from 'ol/style'
import { apiErrorMessage, getAdminGis } from '@/api/client'
import type { DataRow } from '@/types'
import { useAuthStore } from '@/stores/auth'

const mapElement = ref<HTMLElement>()
const auth = useAuthStore()
const scopeLabel = computed(() => auth.isGlobalAdmin ? '全部站点' : `Site ${auth.user?.managed_site_id}`)
const loading = ref(false)
const errorMessage = ref('')
const selectedCampus = ref<number>()
const selectedFeature = ref<{ name: string; properties: Record<string, unknown> }>()
const siteRows = ref<DataRow[]>([]), campusRows = ref<DataRow[]>([]), libraryRows = ref<DataRow[]>([])
const visibility = reactive({ sites: true, campuses: true, libraries: true })
let map: Map | undefined
const siteSource = new VectorSource(), campusSource = new VectorSource(), librarySource = new VectorSource()
const palette = [
  { stroke: 'rgba(41, 216, 199, 1)', siteFill: 'rgba(41, 216, 199, .16)', campusFill: 'rgba(41, 216, 199, .34)' },
  { stroke: 'rgba(87, 151, 255, 1)', siteFill: 'rgba(87, 151, 255, .16)', campusFill: 'rgba(87, 151, 255, .34)' },
  { stroke: 'rgba(169, 139, 255, 1)', siteFill: 'rgba(169, 139, 255, .16)', campusFill: 'rgba(169, 139, 255, .34)' },
]
const siteLayer = new VectorLayer({
  source: siteSource,
  declutter: true,
  style: (feature) => {
    const color = palette[(Number(feature.get('site_id')) - 1) % 3]
    return new Style({
      stroke: new Stroke({ color: color.stroke, width: 3, lineDash: [10, 6] }),
      fill: new Fill({ color: color.siteFill }),
      text: new Text({
        text: String(feature.get('region_name') || ''),
        font: '600 13px "Noto Sans SC"',
        fill: new Fill({ color: '#dffefa' }),
        stroke: new Stroke({ color: 'rgba(4, 15, 26, .95)', width: 4 }),
      }),
      zIndex: 10,
    })
  },
})
const campusLayer = new VectorLayer({
  source: campusSource,
  declutter: true,
  style: (feature) => {
    const color = palette[(Number(feature.get('site_id')) - 1) % 3]
    return new Style({
      stroke: new Stroke({ color: color.stroke, width: 3 }),
      fill: new Fill({ color: color.campusFill }),
      text: new Text({
        text: String(feature.get('campus_name') || ''),
        font: '600 11px "Noto Sans SC"',
        fill: new Fill({ color: '#ffffff' }),
        stroke: new Stroke({ color: 'rgba(4, 15, 26, .95)', width: 3 }),
        overflow: true,
      }),
      zIndex: 20,
    })
  },
})
const libraryLayer = new VectorLayer({
  source: librarySource,
  style: new Style({
    image: new CircleStyle({ radius: 7, fill: new Fill({ color: '#f6b84a' }), stroke: new Stroke({ color: '#fff8df', width: 2.5 }) }),
    zIndex: 30,
  }),
})
siteLayer.setZIndex(10)
campusLayer.setZIndex(20)
libraryLayer.setZIndex(30)

function parseGeoJson(row: DataRow, type: 'site' | 'campus'): Feature | null {
  if (!row.geometry) return null
  try {
    const geometry = new GeoJSON().readGeometry(JSON.parse(String(row.geometry)), {
      dataProjection: 'EPSG:4326',
      featureProjection: 'EPSG:3857',
    })
    if (!geometry) return null
    const feature = new Feature({ geometry })
    const { geometry: _geoJson, ...properties } = row
    feature.setProperties(properties)
    feature.set('featureType', type)
    return feature
  } catch { return null }
}

async function loadMapData() {
  loading.value = true; errorMessage.value = ''
  try {
    const layers = await getAdminGis()
    siteRows.value = layers.sites; campusRows.value = layers.campuses; libraryRows.value = layers.libraries
    siteSource.clear(); campusSource.clear(); librarySource.clear()
    layers.sites.forEach((row: DataRow) => { const f = parseGeoJson(row, 'site'); if (f) siteSource.addFeature(f) })
    layers.campuses.forEach((row: DataRow) => { const f = parseGeoJson(row, 'campus'); if (f) campusSource.addFeature(f) })
    layers.libraries.forEach((row: DataRow) => {
      const feature = new Feature({ geometry: new Point(fromLonLat([Number(row.longitude), Number(row.latitude)])), ...row, featureType: 'library' })
      librarySource.addFeature(feature)
    })
    const extent = campusSource.getExtent(); if (extent && extent.every(Number.isFinite)) map?.getView().fit(extent, { padding: [70, 70, 70, 70], maxZoom: 12, duration: 600 })
  } catch (error) { errorMessage.value = apiErrorMessage(error) }
  finally { loading.value = false }
}

function syncVisibility() { siteLayer.setVisible(visibility.sites); campusLayer.setVisible(visibility.campuses); libraryLayer.setVisible(visibility.libraries) }
function focusCampus(value: number | undefined) {
  if (!value) return
  const feature = campusSource.getFeatures().find((item) => Number(item.get('campus_id')) === value)
  if (feature) map?.getView().fit(feature.getGeometry()!.getExtent(), { padding: [100, 100, 100, 100], maxZoom: 15, duration: 600 })
}

onMounted(async () => {
  map = new Map({ target: mapElement.value, layers: [new TileLayer({ source: new OSM() }), siteLayer, campusLayer, libraryLayer], view: new View({ center: fromLonLat([104.066, 30.67]), zoom: 10.5 }) })
  map.on('singleclick', (event) => {
    const feature = map?.forEachFeatureAtPixel(event.pixel, (item) => item as Feature)
    if (!feature) { selectedFeature.value = undefined; return }
    const props = { ...feature.getProperties() }; delete props.geometry; delete props.geometry; delete props.featureType
    const type = feature.get('featureType'); const name = String(feature.get(type === 'library' ? 'library_name' : type === 'campus' ? 'campus_name' : 'site_name'))
    selectedFeature.value = { name, properties: props }
  })
  await loadMapData()
})
onBeforeUnmount(() => map?.setTarget(undefined))
</script>

<style scoped>
.map-toolbar { min-height: 69px; margin-bottom: 16px; padding: 12px 17px; display: flex; justify-content: space-between; align-items: center; }
.map-heading { display: flex; flex-direction: column; }.map-heading span { color: var(--cyan); font: 8px 'DM Mono'; letter-spacing: .12em; }.map-heading strong { margin-top: 4px; font-size: 14px; }
.map-actions { display: flex; gap: 9px; }
.map-layout { display: grid; grid-template-columns: 255px minmax(0, 1fr); gap: 16px; height: calc(100vh - 205px); min-height: 570px; }
.map-sidebar { overflow-y: auto; }
.layer-list { padding: 11px 16px; border-bottom: 1px solid var(--line); }.layer-list label { display: flex; align-items: center; justify-content: space-between; min-height: 42px; color: #8aa0b4; font-size: 10px; }.layer-list label > span { display: flex; gap: 9px; align-items: center; }
.legend-area { width: 16px; height: 11px; border: 1px dashed var(--cyan); background: rgba(41,216,199,.1); }.legend-area.campus { border-style: solid; border-color: var(--blue); background: rgba(87,151,255,.16); }.legend-point { width: 10px; height: 10px; border-radius: 50%; background: var(--amber); box-shadow: 0 0 8px rgba(246,184,74,.5); }
.map-statistics { display: grid; grid-template-columns: repeat(3, 1fr); padding: 17px 10px; border-bottom: 1px solid var(--line); }.map-statistics div { display: flex; flex-direction: column; align-items: center; border-right: 1px solid var(--line); }.map-statistics div:last-child { border: 0; }.map-statistics strong { font: 500 19px 'DM Mono'; }.map-statistics span { color: #5e788f; font-size: 8px; margin-top: 3px; }
.selected-feature { padding: 17px; }.selected-feature > span { color: #526c83; font: 8px 'DM Mono'; letter-spacing: .12em; }.selected-feature > strong { display: block; margin: 12px 0; font-size: 12px; color: #d4e2ed; }.selected-feature p { color: #5d768b; font-size: 10px; line-height: 1.8; }.selected-feature dl { margin: 0; }.selected-feature dl > * { display: inline-block; padding: 5px 0; margin: 0; font-size: 8px; border-bottom: 1px solid rgba(151,179,207,.06); }.selected-feature dt { width: 43%; color: #587289; }.selected-feature dd { width: 57%; color: #93a8ba; word-break: break-all; }
.map-canvas { position: relative; overflow: hidden; }.map-host { width: 100%; height: 100%; background: #0a1928; }.map-host :deep(.ol-zoom) { top: 15px; left: 15px; }.map-host :deep(.ol-control button) { background: #0d2032; color: #aac1d4; }.map-corner { position: absolute; right: 14px; bottom: 14px; display: flex; flex-direction: column; padding: 9px 12px; background: rgba(7,17,31,.88); border: 1px solid var(--line); border-radius: 6px; }.map-corner span { color: var(--cyan); font: 8px 'DM Mono'; }.map-corner i { display: inline-block; width: 5px; height: 5px; background: var(--cyan); border-radius: 50%; margin-right: 6px; }.map-corner small { color: #506980; font-size: 8px; margin-top: 3px; }.map-error { position: absolute; left: 50%; top: 20px; transform: translateX(-50%); padding: 9px 13px; color: #ffc2c9; background: rgba(80,20,30,.9); border: 1px solid rgba(255,110,125,.25); border-radius: 6px; font-size: 10px; }
@media (max-width: 760px) { .map-toolbar { align-items: flex-start; gap: 12px; flex-direction: column; }.map-actions { width: 100%; }.map-actions .el-select { flex: 1; }.map-layout { grid-template-columns: 1fr; height: auto; }.map-sidebar { max-height: none; }.selected-feature { display: none; }.map-canvas { height: 520px; } }
</style>
