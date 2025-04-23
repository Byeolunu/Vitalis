module.exports = {
    content: ['./ht/**/*.html'],

    darkMode: 'class',

    theme: {
        extend: {
            colors: {
                red: '#bd2c49',
                secondary: '#5e89ab',
                third: '#afc2cc',
                white: '#ffffff',
                text: '#0a0803',
            },

            fontFamily: {
                head: ['Pixelify', 'sans-serif'],
                body: ['Poppins', 'sans-serif'],
            },

            cursor: {
                mi: 'url(assets/star-4pt-round.png), auto',
            },

            keyframes: {
                typewrite: {
                    from: { width: '0', borderRight: '3px solid black' },
                    to: { width: '100%', borderRight: '3px solid transparent' },
                },

                blink: {
                    '0%, 100%': { borderColor: 'transparent' },
                    '50%': { borderColor: 'black' },
                },
            },

            animation: {
                typewrite: 'typewrite 4s steps(30) forwards',
                blink: 'blink 0.7s infinite',
            },

            backgroundImage: {
                'myimg': "url('../assets/ChatGPT Image 18 avr. 2025, 00_01_52.png')",
            },
        },
    },

    plugins: [],
}


// module.exports = {

//         content: ['./ht/**/*.html'],
    
//         darkMode: 'class',
    
//         theme: {
    
//             extend: {
    
//                 colors: {
    
//                     primary: 'caf0f8',
    
//                     secondary: '#03045e',
    
//                     third: '#023e8a',
    
//                     fourth: '#0077b6',
    
//                     fifth:'#48cae4',
    
//                     sixth: '#90e0ef',
    
//                     text: '#2e2e2e',
    
//                     yelloww: '#ffb703',
    
      
    
//                 },
    
//                 fontFamily: {
    
//                     head: ['Pixelify', 'sans-serif'],
    
//                     body: ['Poppins', 'sans-serif'],
    
//                 },
    
//                 cursor: {
    
//                     mi: 'url(assets/star-4pt-round.png), auto',
    
//                 },
    
//                 keyframes: {
    
//                     typewrite: {
    
//                         from: { width: '0', borderRight: '3px solid black' },
    
//                         to: { width: '100%', borderRight: '3px solid transparent' },
    
//                     },
    
//                     blink: {
    
//                         '0%, 100%': { borderColor: 'transparent' },
    
//                         '50%': { borderColor: 'black' },
    
//                     },
    
//                 },
    
//                 animation: {
    
//                     typewrite: 'typewrite 4s steps(30) forwards',
    
//                     blink: 'blink 0.7s infinite',
    
//                 },
    
//                 backgroundImage: {
    
//                     'myimg':"url('../assets/ChatGPT Image 18 avr. 2025, 00_01_52.png')",
    
//                 },
    
//                 },
    
//         },
    
//         plugins: [],
    
//     }
    