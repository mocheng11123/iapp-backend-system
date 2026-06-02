import api from '@/utils/request'

export interface Announcement {
  id: string
  title: string
  content: string
  is_sticky: boolean
  start_at?: string
  end_at?: string
  created_at: string
}

export function createAnnouncement(data: any) {
  return api.post<Announcement>('/dev/announcements', data)
}

export function getAnnouncements(appId?: string) {
  return api.get<Announcement[]>('/dev/announcements', { params: { app_id: appId } })
}

export function deleteAnnouncement(id: string) {
  return api.delete(`/dev/announcements/${id}`)
}

export interface Version {
  id: string
  version_code: number
  version_name: string
  update_log?: string
  download_url: string
  force_update: boolean
}

export function createVersion(data: any) {
  return api.post<Version>('/dev/versions', data)
}

export function getVersions() {
  return api.get<Version[]>('/dev/versions')
}

export function deleteVersion(id: string) {
  return api.delete(`/dev/versions/${id}`)
}

export interface Splash {
  id: string
  image_url: string
  platform: string
  priority: number
  start_at?: string
  end_at?: string
}

export function createSplash(data: any) {
  return api.post<Splash>('/dev/splash', data)
}

export function getSplashes() {
  return api.get<Splash[]>('/dev/splash')
}

export interface Ad {
  id: string
  slot: string
  type: string
  media_url: string
  target_url?: string
  weight: number
  status: number
}

export function createAd(data: any) {
  return api.post<Ad>('/dev/ads', data)
}

export function getAds() {
  return api.get<Ad[]>('/dev/ads')
}
