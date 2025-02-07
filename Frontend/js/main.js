
async function getCountries() {
    try {
      const response = await fetch('http://localhost:8000/');
      const data = await response.json();
      fillCountries(data.datos, "España");
    } catch (error) {
        console.error('Error:', error);
    }
  }
  
getCountries();

function fillCountries(listOfCountries, defaultCountry){
    const select = document.getElementById("country");

    listOfCountries.forEach(country => {
        const option = document.createElement("option");
        option.value = country;
        option.text = country;

        if(country === defaultCountry){
            option.selected ="selected"
        }
        select.appendChild(option);
    });
}

// Función para mostrar el spinner
function showSpinner() {
    const spinnerContainer = document.createElement("div");
    spinnerContainer.classList.add("spinner-container");
    const spinner = document.createElement("div");
    spinner.classList.add("spinner");
    spinnerContainer.appendChild(spinner);
    document.body.appendChild(spinnerContainer);
  }
  
  // Función para ocultar el spinner
  function hideSpinner() {
    const spinnerContainer = document.querySelector(".spinner-container");
    if (spinnerContainer) {
      spinnerContainer.remove();
    }
  }
  
  // Modifica la función submitForm para mostrar el spinner antes de enviar la petición
  async function submitForm() {
    showSpinner(); // Mostrar el spinner
    const form = document.getElementById('travelForm');
    const formData = new FormData(form);
    const URL = 'http://localhost:8000/servidor';
    const data = {
      origin: formData.get('origin'),
      country: formData.get('country'),
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
      hideSpinner(); // Ocultar el spinner
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
          const ANSWER = await response.json();
          console.log(ANSWER);
          const UL = document.getElementById("screen_text");
  
          let tiempo = 0;
          ANSWER.datos.forEach(linea => {
            setTimeout(() => {
              let li = document.createElement("li");
              li.appendChild(document.createTextNode(formateoTexto(linea)));
              UL.appendChild(li);
              UL.lastElementChild.scrollIntoView({ behavior: 'smooth' });
            }, tiempo);
            tiempo += 300;
          });
          hideSpinner(); // Ocultar el spinner
        } else {
          alert('Error al enviar los datos');
          hideSpinner(); // Ocultar el spinner
        }
      } catch (error) {
        console.error('Error:', error);
        alert('No se pudo conectar con el servidor');
        hideSpinner(); // Ocultar el spinner
      }
    }
  }
  

function formateoTexto(linea){
    let textoFormateado = linea.replace(/\*\*(\w+)\*\*/g, (match, grupo) => `<b>${grupo.toUpperCase()}</b><br>`);
    console.log(textoFormateado)
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
  

function showSpinner() {
    const spinnerContainer = document.createElement("div");
    spinnerContainer.classList.add("spinner-container");
    const spinner = document.createElement("div");
    spinner.classList.add("spinner");
    spinnerContainer.appendChild(spinner);
    document.body.appendChild(spinnerContainer);
  }
  
  // Función para ocultar el spinner
  function hideSpinner() {
    const spinnerContainer = document.querySelector(".spinner-container");
    if (spinnerContainer) {
      spinnerContainer.remove();
    }
  }