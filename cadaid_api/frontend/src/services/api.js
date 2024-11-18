const API_URL = 'http://cadaid-api.westeurope.azurecontainer.io'

const API_KEY = import.meta.env.VITE_API_KEY

console.log('API Configuration:', {
  url: API_URL,
  keyPresent: !!API_KEY,
  keyLength: API_KEY?.length
})

class ApiService {
  async uploadAndProcess(files) {
    try {
      console.log('Starting upload process for files:', files.length)
      const formData = new FormData()
      Array.from(files).forEach(file => {
        console.log('Adding file to form:', file.name, file.type, file.size)
        formData.append('uploaded_files', file, file.name)
      })

      console.log('Sending request to API:', `${API_URL}/detect/`)
      console.log('Request headers:', {
        'Accept': 'application/json',
        'X-API-KEY': API_KEY ? 'present' : 'missing'
    })

      const response = await fetch(`${API_URL}/detect/`, {
        method: 'POST',
        headers: {
          'Accept': 'application/json',
          'X-API-KEY': API_KEY
        },
        body: formData,
        mode: 'cors'
      })

      console.log('Response status:', response.status)
      console.log('Response headers:', Object.fromEntries(response.headers.entries()))

      if (!response.ok) {
        const errorText = await response.text()
        console.error('Error response body:', errorText)
        throw new Error(`HTTP error! status: ${response.status}, message: ${errorText}`)
      }

      const data = await response.json()
      console.log('Response data:', data)
      
      return data.map((result, index) => {
        console.log('Processing result for file ${index}:', files[index].name)
        return {
          ...result,
          filename: files[index].name,
          imageUrl: URL.createObjectURL(files[index])
        }
      })
    } catch (error) {
      console.error('Upload error details:', {
        message: error.message,
        stack: error.stack,
        type: error.name
      })
      throw error
    }
  }

  async submitFeedback(feedback) {
    try {
      console.log('Submitting feedback:', feedback)
      const formData = new FormData()
      formData.append('filename', feedback.filename.trim())
      
      const isPositiveFeedback = Object.values(feedback.feedback).some(value => value === true)
      formData.append('user_response', isPositiveFeedback.toString())

      console.log('Sending request to API:', `${API_URL}/feedback/`)
      console.log('Feedback form data:', Object.fromEntries(formData.entries()))
      
      const response = await fetch(`${API_URL}/feedback/`, {
        method: 'POST',
        headers: {
          'Accept': 'application/json',
          'X-API-KEY': API_KEY
        },
        body: formData,
        mode: 'cors'
      })

      console.log('Feedback response status:', response.status)
      console.log('Feedback response headers:', Object.fromEntries(response.headers.entries()))

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

