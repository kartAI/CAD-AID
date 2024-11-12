const API_URL = 'http://localhost:8000'

class ApiService {
  async uploadAndProcess(files) {
    try {
      const formData = new FormData()
      Array.from(files).forEach(file => {
        formData.append('uploaded_files', file, file.name)
      })

      const response = await fetch(`${API_URL}/detect`, {
        method: 'POST',
        body: formData
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const data = await response.json()
      
      // Transform the response to include image URLs and file previews
      return data.map((result, index) => ({
        ...result,
        filename: files[index].name,
        imageUrl: URL.createObjectURL(files[index])
      }))
    } catch (error) {
      console.error('Upload error:', error)
      throw error
    }
  }

  async submitFeedback(feedback) {
    try {
      const formData = new FormData()
      formData.append('filename', feedback.filename)
      formData.append('user_response', feedback.user_response)

      const response = await fetch(`${API_URL}/feedback`, {
        method: 'POST',
        body: formData
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      return await response.json()
    } catch (error) {
      console.error('Feedback error:', error)
      throw error
    }
  }
}

export default new ApiService()
