/* global use, db */
// MongoDB Playground
// To disable this template go to Settings | MongoDB | Use Default Template For Playground.
// Make sure you are connected to enable completions and to be able to run a playground.
// Use Ctrl+Space inside a snippet or a string literal to trigger completions.
// The result of the last command run in a playground is shown on the results panel.
// By default the first 20 documents will be returned with a cursor.
// Use 'console.log()' to print to the debug output.
// For more documentation on playgrounds please refer to
// https://www.mongodb.com/docs/mongodb-vscode/playgrounds/

// Select the database to use.
use('smart-fitness');

db.getCollection("challenge_history").find({})

// db.getCollection("challenge_history").deleteMany({})
// db.getCollection("users").deleteMany({})
// db.getCollection("user_history").deleteMany({})
// db.getCollection("workouts").deleteMany({})

// db.createCollection("challenge_history")

// db.challenge_history.insert([
//     {
//         "username":"john_doe",
//         "title" : "",
//         "completedOn" : ""
//     }
// ])

// db.runCommand(
//     {
//         createIndexes : "challenge_history",
//         indexes: [
//             {
//                 name:"usernameVectorSearchIndex",
//                 key: {
//                     "username": "cosmosSearch" 
//                 },
//                 cosmosSearchOptions: {
//                     kind: "vector-ivf",
//                     numLists: 1,
//                     similarity: "COS",
//                     dimensions: 1536
//                 }
                
//             },
//             {
//                 name:"titleVectorSearchIndex",
//                 key: {
//                     "title": "cosmosSearch" 
//                 },
//                 cosmosSearchOptions: {
//                     kind: "vector-ivf",
//                     numLists: 1,
//                     similarity: "COS",
//                     dimensions: 1536
//                 }
                
//             },
//             {
//                 name:"completedOnVectorSearchIndex",
//                 key: {
//                     "completedOn": "cosmosSearch" 
//                 },
//                 cosmosSearchOptions: {
//                     kind: "vector-ivf",
//                     numLists: 1,
//                     similarity: "COS",
//                     dimensions: 1536
//                 }
                
//             }
//         ]
//     }
// )

// db.createCollection("user_history")

// // db.runCommand(
// //     {
// //         createIndexes : "user_history",
// //         indexes: [
// //             {
// //                 name:"dateVectorSearchIndex",
// //                 key: {
// //                     "date": "cosmosSearch" 
// //                 },
// //                 cosmosSearchOptions: {
// //                     kind: "vector-ivf",
// //                     numLists: 1,
// //                     similarity: "COS",
// //                     dimensions: 1536
// //                 }
                
// //             },
// //             {
// //                 name:"current_weightVectorSearchIndex",
// //                 key: {
// //                     "current_weight": "cosmosSearch" 
// //                 },
// //                 cosmosSearchOptions: {
// //                     kind: "vector-ivf",
// //                     numLists: 1,
// //                     similarity: "COS",
// //                     dimensions: 1536
// //                 }
                
// //             },
// //             {
// //                 name:"usernameVectorSearchIndex",
// //                 key: {
// //                     "username": "cosmosSearch" 
// //                 },
// //                 cosmosSearchOptions: {
// //                     kind: "vector-ivf",
// //                     numLists: 1,
// //                     similarity: "COS",
// //                     dimensions: 1536
// //                 }
                
// //             }
// //         ]
// //     }
// // )

// // db.createCollection("challenges")

// // db.challenges.insertMany([
// //     {
// //         "title": "1500 Calorie Sizzle",
// //         "description" : "Burn 1500 calories in a week",
// //         "duration" : 7,
// //         "calories" : 1500, 
// //         "type" : "Weekly"

// //     },
// //     {
// //         "title": "2000 Calorie Roast",
// //         "description" : "Burn 2000 calories in a week",
// //         "duration" : 7,
// //         "calories" : 2000, 
// //         "type" : "Weekly"

// //     },
// //     {
// //         "title": "3000 Calorie Fry",
// //         "description" : "Burn 3000 calories in a week",
// //         "duration" : 7,
// //         "calories" : 1500, 
// //         "type" : "Weekly"

// //     },
// //     {
// //         "title": "20-Day Active",
// //         "description" : "Track 20 days of workouts",
// //         "duration" : 28,
// //         "type" : "Monthly"
// //     },
// //     {
// //         "title": "10000 Calorie Blaze",
// //         "description" : "Burn 10000 calories in a month",
// //         "duration" : 28,
// //         "calories" : 10000, 
// //         "type" : "Monthly"

// //     }
// // ])

// db.runCommand(
//     {
//         createIndexes : "challenges",
//         indexes: [
//             {
//                 name:"titleVectorSearchIndex",
//                 key: {
//                     "title": "cosmosSearch" 
//                 },
//                 cosmosSearchOptions: {
//                     kind: "vector-ivf",
//                     numLists: 1,
//                     similarity: "COS",
//                     dimensions: 1536
//                 }
                
//             }, 
//             {
//                 name: "descriptionVectorSearchIndex",  // Replace with your actual index name
//                 key: {
//                     "description": "cosmosSearch"  // Replace "vectorColumn" with your actual vector column name
//                 },
//                 cosmosSearchOptions: {
//                     kind: "vector-ivf",
//                     numLists: 1,
//                     similarity: "COS",
//                     dimensions: 1536
//                 }
//             }, 
//             {
//                 name: "typeVectorSearchIndex",  // Replace with your actual index name
//                 key: {
//                     "type": "cosmosSearch"  // Replace "vectorColumn" with your actual vector column name
//                 },
//                 cosmosSearchOptions: {
//                     kind: "vector-ivf",
//                     numLists: 1,
//                     similarity: "COS",
//                     dimensions: 1536
//                 }
//             }, 
//             {
//                 name: "durationVectorSearchIndex",  // Replace with your actual index name
//                 key: {
//                     "duration": "cosmosSearch"  // Replace "vectorColumn" with your actual vector column name
//                 },
//                 cosmosSearchOptions: {
//                     kind: "vector-ivf",
//                     numLists: 1,
//                     similarity: "COS",
//                     dimensions: 1536
//                 }
//             }, 
//             {
//                 name: "caloriesVectorSearchIndex",  // Replace with your actual index name
//                 key: {
//                     "calories": "cosmosSearch"  // Replace "vectorColumn" with your actual vector column name
//                 },
//                 cosmosSearchOptions: {
//                     kind: "vector-ivf",
//                     numLists: 1,
//                     similarity: "COS",
//                     dimensions: 1536
//                 }
//             }
//         ]
//     }
// )