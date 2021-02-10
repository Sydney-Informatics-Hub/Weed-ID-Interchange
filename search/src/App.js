import React, { Component } from 'react'
import { Route, Switch, Redirect } from "react-router-dom"
import { withRouter } from "react-router"
import {ThemeProvider} from '@material-ui/styles'
import NavbarComponent from './Components/wrapper/navbar'
import { Standalone as AgContextEditor } from './AgContextForm'
import theme from './Components/ui/theme'
import './App.css'

class App extends Component {
	render() {
		return (
			<ThemeProvider theme={theme}>
				<Switch>
					<Redirect exact from="/" to="/explore" />
					<Route exact path='/editor' component={AgContextEditor} />
					<Route exact path="/:page/:dataset_id?" render={props => <NavbarComponent {...props} />} />
				</Switch>
			</ThemeProvider>
		);
	}
}

export default withRouter(App);
