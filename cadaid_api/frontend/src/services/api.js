const API_URL = 'http://localhost'

class ApiService {
  async uploadAndProcess(files) {
    try {
      const formData = new FormData()
      Array.from(files).forEach(file => {
        formData.append('uploaded_files', file, file.name)
      })

      const response = await fetch(`${API_URL}/detect/`, {
        method: 'POST',
        headers: {
          'Accept': 'application/json',
        },
        body: formData,
        mode: 'cors'
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const data = await response.json()
      
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
      formData.append('filename', feedback.filename.trim())
      
      const isPositiveFeedback = Object.values(feedback.feedback).some(value => value === true)
      formData.append('user_response', isPositiveFeedback.toString())
      
      const response = await fetch(`${API_URL}/feedback/`, {
        method: 'POST',
        headers: {
          'Accept': 'application/json',
        },
        body: formData,
        mode: 'cors',
        credentials: 'include'
      })

      if (!response.ok) {
        const errorText = await response.text()
        console.error('Feedback submission failed:', errorText)
        throw new Error(`HTTP error! status: ${response.status}, message: ${errorText}`)
      }
      return await response.json()
    } catch (error) {
      console.error('Feedback error:', error)
      throw error
    }
  }
}

export default new ApiService()

