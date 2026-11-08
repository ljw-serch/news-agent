import request from '@/utils/request'

export function uploadFileApi(file) {
  const formData = new FormData()
  formData.append('file', file)
  return request({
    url: '/api/files/upload',
    method: 'post',
    data: formData,
    timeout: 60000
  })
}
