
async function getCountries() {
    try {
      const response = await fetch('http://localhost:8000/');
      const data = await response.json();
      console.log(data);
      console.log(data.datos)
      fillCountries(data.datos);
    } catch (error) {
        fillCountries(['Alemania','Francia']);
      console.error('Error:', error);
    }
  }
  
getCountries();

function fillCountries(listOfCountries){
    const select = document.getElementById("destination");

    listOfCountries.forEach(country => {
        const option = document.createElement("option");
        option.value = country;
        option.text = country;
        select.appendChild(option);
    });
}

//Envio al back
async function submitForm() {
    const form = document.getElementById('travelForm');
    const formData = new FormData(form);
    const URL = 'http://localhost:8000/servidor';
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
  
    if (!validateDates(data.departureDate, data.returnDate)) {
      alert('Fechas inválidas. Por favor, indique unas fechas correctas.');
    } else {
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

          //Añadir respuesta al front
          const ANSWER = await response.json();
          console.log(ANSWER)
        //   const B = JSON.stringify(ANSWER)
        //   console.log(B)
        const TEXT = document.getElementById("screen_text");
        console.log(TEXT)
        let li = document.createElement("li");
        li.appendChild(document.createTextNode(ANSWER.mensaje))
        TEXT.appendChild(li)
        } else {
          alert('Error al enviar los datos');
        }
      } catch (error) {
        console.error('Error:', error);
        alert('No se pudo conectar con el servidor');
      }
    }
}

//Validar fechas
function validateDates(departureDate, returnDate) {
// Verificar si ambas fechas son válidas
if (!isValidDate(departureDate) || !isValidDate(returnDate)) {
    return false;
}
// Convertir las fechas a objetos Date
const departureDateObj = new Date(departureDate);
const returnDateObj = new Date(returnDate);
const today = new Date();
today.setHours(0, 0, 0, 0); // Establecer la hora a medianoche para comparar solo la fecha
// Verificar si la fecha de salida es hoy o posterior
if (departureDateObj < today) {
    alert('La fecha de salida debe ser hoy o posterior.');
    return false;
}
// Verificar si la fecha de regreso es mayor o igual que la fecha de partida
if (returnDateObj < departureDateObj) {
    alert('La fecha de regreso debe ser mayor o igual que la fecha de partida.');
    return false;
}
return true;
}
  
// Función auxiliar para verificar si una fecha es válida
function isValidDate(dateString) {
const regex = /^\d{4}-\d{2}-\d{2}$/;
if (!regex.test(dateString)) {
    return false;
}
const dateParts = dateString.split('-');
const year = parseInt(dateParts[0], 10);
const month = parseInt(dateParts[1], 10);
const day = parseInt(dateParts[2], 10);
const date = new Date(year, month - 1, day);
return date.getFullYear() === year && date.getMonth() === month - 1 && date.getDate() === day;
}
  