# 🎧 Model Card: Music Recommender Simulation

## 1. Model Name  

Give your model a short, descriptive name.  
Example: **VibeFinder 1.0**  

---

## 2. Intended Use  

Describe what your recommender is designed to do and who it is for. 

Prompts:  

- What kind of recommendations does it generate  
- What assumptions does it make about the user  
- Is this for real users or classroom exploration  

---

## 3. How the Model Works  

My recommender looks at four things about each song: its genre, mood, how energetic and how acoustic it is. The recommender then compares them to what a listener says they like. Genre and mood are simple yes/no matches: the song either fits your favorite or not. Energy is judged by closeness: a song whose energy is near your target scores well, and the further away it is the less it scores. 
The system adds these up into a single number for each song, then sorts every song by that number and shows you the highest.

---

## 4. Data  

The catalog starts as a CSV of songs, each described by attributes like genre, mood, energy, tempo, valence, danceability, and acousticness. (Note: the starter has 10 songs; I will expand it to at least 15–20 in the design phase.)

A limitation worth naming early: this is a very small catalog that cannot represent the full range of musical taste (let alone music), and it only models one user at a time.

---

## 5. Strengths  

Where does your system seem to work well  

Prompts:  

- User types for which it gives reasonable results  
- Any patterns you think your scoring captures correctly  
- Cases where the recommendations matched your intuition  

---

## 6. Limitations and Bias 

Where the system struggles or behaves unfairly. 

Prompts:  

- Features it does not consider  
- Genres or moods that are underrepresented  
- Cases where the system overfits to one preference  
- Ways the scoring might unintentionally favor some users  

---

## 7. Evaluation  

How you checked whether the recommender behaved as expected. 

Prompts:  

- Which user profiles you tested  
- What you looked for in the recommendations  
- What surprised you  
- Any simple tests or comparisons you ran  

No need for numeric metrics unless you created some.

---

## 8. Future Work  

Ideas for how you would improve the model next.  

Prompts:  

- Additional features or preferences  
- Better ways to explain recommendations  
- Improving diversity among the top results  
- Handling more complex user tastes  

---

## 9. Personal Reflection  

A few sentences about your experience.  

Prompts:  

- What you learned about recommender systems  
- Something unexpected or interesting you discovered  
- How this changed the way you think about music recommendation apps  
