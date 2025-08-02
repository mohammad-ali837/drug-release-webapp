from flask import Flask, render_template_string, request
import numpy as np
import matplotlib.pyplot as plt
import io
import base64

app = Flask(__name__)

HTML = '''
<!doctype html>
<title>Drug Release Q Calculator</title>
<h2>Calculate Q based on ε</h2>
<form method=post>
  D (Diffusion coefficient): <input type=text name=D value="1e-6"><br><br>
  τ (Tortuosity): <input type=text name=tau value="1.5"><br><br>
  A (Effective surface area): <input type=text name=A value="2.0"><br><br>
  Cs (Saturation concentration): <input type=text name=Cs value="0.1"><br><br>
  t (Time in seconds): <input type=text name=t value="3600"><br><br>
  <input type=submit value=Calculate>
</form>

{% if table %}
  <h3>Results:</h3>
  {{ table|safe }}
  <br><br>
  <img src="data:image/png;base64,{{ plot_url }}">
  <h3>Analysis:</h3>
  <pre>{{ analysis }}</pre>
{% endif %}
'''

def calculate_Q(D, epsilon, tau, A, Cs, t):
    term = (D * epsilon / tau) * (2 * A - epsilon * Cs) * Cs * t
    if term < 0:
        return 0
    return term ** 0.5

def analyze_Q_behavior(epsilon_values, Q_values):
    max_Q = max(Q_values)
    max_epsilon = epsilon_values[Q_values.index(max_Q)]
    increasing = all(x <= y for x, y in zip(Q_values, Q_values[1:]))

    analysis = ""
    analysis += "Analysis of ε effect on Q:\n"
    analysis += "- Q increases with ε initially and may plateau or decrease afterwards.\n"
    analysis += f"- Maximum Q value is {max_Q:.6f} at ε = {max_epsilon:.2f}.\n"
    if increasing:
        analysis += "- Q shows an approximately monotonic increase with ε.\n"
    else:
        analysis += "- Q shows a nonlinear trend with a maximum point.\n"
    return analysis

@app.route('/', methods=['GET', 'POST'])
def index():
    table = None
    plot_url = None
    analysis = None

    if request.method == 'POST':
        try:
            D = float(request.form['D'])
            tau = float(request.form['tau'])
            A = float(request.form['A'])
            Cs = float(request.form['Cs'])
            t = float(request.form['t'])
        except ValueError:
            return render_template_string(HTML, table=None, plot_url=None, analysis="Please enter valid numeric values.")

        epsilon_values = [i/100 for i in range(1, 90)]
        Q_values = [calculate_Q(D, e, tau, A, Cs, t) for e in epsilon_values]

        rows = "".join(f"<tr><td>{e:.2f}</td><td>{q:.6f}</td></tr>" for e, q in zip(epsilon_values, Q_values))
        table = f'''
        <table border="1" cellpadding="5" cellspacing="0">
            <tr><th>Epsilon (ε)</th><th>Q (Drug released)</th></tr>
            {rows}
        </table>
        '''

        fig, ax = plt.subplots()
        ax.plot(epsilon_values, Q_values, marker='o')
        ax.set_xlabel('Epsilon (ε)')
        ax.set_ylabel('Q (Drug released)')
        ax.set_title('Effect of ε on Q')
        ax.grid(True)

        img = io.BytesIO()
        plt.savefig(img, format='png')
        plt.close(fig)
        img.seek(0)
        plot_url = base64.b64encode(img.getvalue()).decode()

        analysis = analyze_Q_behavior(epsilon_values, Q_values)

    return render_template_string(HTML, table=table, plot_url=plot_url, analysis=analysis)
if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
