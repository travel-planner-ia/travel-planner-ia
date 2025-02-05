async function submitForm() {
    const form = document.getElementById('travelForm');
    const formData = new FormData(form);
    const URL = 'http://localhost:3000/'
    
    const data = {
      destination: formData.get('destination'),
      adults: formData.get('adults'),
      children: formData.get('children'),
      departureDate: formData.get('departureDate'),
      returnDate: formData.get('returnDate'),
      budget: formData.get('budget'),
      medicalCondition: formData.get('medicalCondition'),
      additionalInfo: formData.get('additionalInfo'),
      tags: formData.getAll('tags')
    };
  
    try {
      const response = await fetch(URL, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
      });
  
      if (response.ok) {
        alert('Datos enviados con éxito');
      } else {
        alert('Error al enviar los datos');
      }
    } catch (error) {
      console.error('Error:', error);
      alert('No se pudo conectar con el servidor');
    }
  }
